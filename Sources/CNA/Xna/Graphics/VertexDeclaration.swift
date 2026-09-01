// SPDX-License-Identifier: MIT

extension Microsoft.Xna.Framework.Graphics {
    /// The internal `VertexElementValidator`, which is where every
    /// `VertexDeclaration` argument failure comes from.
    ///
    /// `assembly` in the metadata, so it is not a contract type and is not
    /// projected as one; it is reproduced here because the two public
    /// constructors call it and its behaviour is theirs.
    internal enum VertexElementValidator {
        /// The four `FrameworkResources` templates this validator reproduces,
        /// read out of `Microsoft.Xna.Framework.dll`'s own embedded string
        /// table and pinned in
        /// `tools/api_compat/reference/xna40-selected-resource-strings.json`.
        ///
        /// A fifth, `VertexElementBadUsage`, is deliberately absent: see
        /// `validate(vertexStride:elements:)`.
        internal static let offsetNotMultipleFour =
            "Invalid VertexDeclaration. Vertex stride and VertexElement.Offset "
            + "must be multiples of four."
        internal static let outsideStride =
            "Invalid VertexDeclaration. Element {0}{1} does not fit within the "
            + "specified vertex stride."
        internal static let elementsOverlap =
            "Invalid VertexDeclaration. Elements {0}{1} and {2}{3} are "
            + "overlapping."
        internal static let duplicateElement =
            "Invalid VertexDeclaration. Duplicate element {0}{1}."

        /// `String.Format(CurrentCulture, template, args)` over the positional
        /// placeholders these four templates use. The arguments are boxed
        /// enum and `Int32` values in the CLR, so each is formatted with its
        /// own `ToString()` — the enum's case name and the integer's digits.
        internal static func format(
            _ template: String, _ arguments: String...
        ) -> String {
            var result = template
            for (index, argument) in arguments.enumerated() {
                result = result.replacingOccurrences(
                    of: "{\(index)}", with: argument)
            }
            return result
        }
        /// `GetTypeSize(VertexElementFormat)` — a switch with a default of 0.
        ///
        /// The default is unreachable through the Swift enum, which has no
        /// case outside the twelve, but it is the CLR's answer and is written
        /// down rather than assumed away.
        internal static func typeSize(
            _ format: Microsoft.Xna.Framework.Graphics.VertexElementFormat
        ) -> Int32 {
            switch format {
            case .Single: return 4
            case .Vector2: return 8
            case .Vector3: return 12
            case .Vector4: return 16
            case .Color: return 4
            case .Byte4: return 4
            case .Short2: return 4
            case .Short4: return 8
            case .NormalizedShort2: return 4
            case .NormalizedShort4: return 8
            case .HalfVector2: return 4
            case .HalfVector4: return 8
            }
        }

        /// `GetVertexStride(VertexElement[])`.
        ///
        /// The **maximum end offset**, not a sum and not the last element's
        /// end: elements may be given in any order and may overlap, and an
        /// empty array answers zero.
        internal static func vertexStride(
            _ elements: [Microsoft.Xna.Framework.Graphics.VertexElement]
        ) -> Int32 {
            var maximum: Int32 = 0
            for element in elements {
                let end = element.Offset + typeSize(element.VertexElementFormat)
                if maximum < end { maximum = end }
            }
            return maximum
        }

        /// `Validate(int32 vertexStride, VertexElement[] elements)`.
        ///
        /// The order of the checks is observable and is reproduced exactly: an
        /// element that is both misaligned and overlapping reports the
        /// alignment message, and one that is both outside the stride and
        /// misaligned reports the stride message. Overlap is decided with a
        /// map carrying one slot per byte of the vertex, each tagged with the
        /// index of the element that owns it — which is why that message can
        /// name **both** offending elements.
        ///
        /// XNA's first per-element check, `VertexElementBadUsage`, is
        /// **unreachable here**: `VertexElementUsage` is a Swift enum with
        /// thirteen cases and no way to hold a value outside `0...12`, so the
        /// type system enforces what XNA enforces at run time. Its message is
        /// therefore not reproduced and is deliberately not pinned.
        internal static func validate(
            vertexStride: Int32,
            elements: [Microsoft.Xna.Framework.Graphics.VertexElement]
        ) throws {
            guard vertexStride > 0 else {
                throw CNAArgumentOutOfRangeException(paramName: "vertexStride")
            }
            guard vertexStride & 3 == 0 else {
                throw CNAArgumentException(
                    message: VertexElementValidator.offsetNotMultipleFour)
            }
            var owner = [Int](repeating: -1, count: Int(vertexStride))
            for index in elements.indices {
                let element = elements[index]
                let size = typeSize(element.VertexElementFormat)
                guard element.Offset >= 0,
                      element.Offset + size <= vertexStride else {
                    throw CNAArgumentException(
                        message: format(
                            outsideStride,
                            String(describing: element.VertexElementUsage),
                            String(element.UsageIndex)))
                }
                guard element.Offset & 3 == 0 else {
                    throw CNAArgumentException(
                        message: VertexElementValidator.offsetNotMultipleFour)
                }
                // Only the elements BEFORE this one are compared, so the pair
                // is always reported with the later element's own identity.
                for earlier in elements[..<index] where
                    earlier.VertexElementUsage == element.VertexElementUsage
                    && earlier.UsageIndex == element.UsageIndex {
                    throw CNAArgumentException(
                        message: format(
                            duplicateElement,
                            String(describing: element.VertexElementUsage),
                            String(element.UsageIndex)))
                }
                for byte in Int(element.Offset)..<Int(element.Offset + size) {
                    guard owner[byte] < 0 else {
                        let held = elements[owner[byte]]
                        throw CNAArgumentException(
                            message: format(
                                elementsOverlap,
                                String(describing: held.VertexElementUsage),
                                String(held.UsageIndex),
                                String(describing: element.VertexElementUsage),
                                String(element.UsageIndex)))
                    }
                    owner[byte] = index
                }
            }
        }
    }

    /// The `Microsoft.Xna.Framework.Graphics.VertexDeclaration` projection.
    ///
    /// A `GraphicsResource` with **no native object**. CNA does publish
    /// `cna_vertex_declaration_create` and its neighbours, and none of them
    /// takes a device — but nothing in this type's own public surface needs a
    /// native handle, and binding a route with no member behind it is what
    /// `docs/native-abi.md` forbids. The routes are bound when a consumer of a
    /// declaration exists.
    open class VertexDeclaration: GraphicsResource {
        // `_elements`. Optional because XNA's constructors leave the field
        // NULL for a null or empty array, which is a state `GetVertexElements`
        // then dereferences.
        private let storedElements: [VertexElement]?
        private let storedStride: Int32

        /// `VertexDeclaration..ctor(Int32 vertexStride, VertexElement[] elements)`.
        ///
        /// An **empty** array is accepted in silence and leaves the
        /// declaration with no elements and a stride of zero — the IL's two
        /// `leave` instructions, not an oversight. Otherwise the array is
        /// copied, the stride is stored, and the pair is validated.
        ///
        /// XNA's null case is not reachable through a Swift `[VertexElement]`,
        /// and the empty case reproduces it exactly: both leave by the same
        /// branch, before any field is written.
        ///
        /// XNA wraps the body in a `fault` handler that calls `Dispose(true)`
        /// when `Validate` throws. This validates after `super.init`, so a
        /// failed construction leaves a fully initialised object that Swift
        /// deinits instead. The difference is not observable: `Disposing`
        /// cannot have a subscriber, because the initializer has not returned
        /// and no reference has escaped; there is no native storage to
        /// release; and `GraphicsResource.Dispose(Boolean)` does nothing else.
        public init(
            vertexStride: Int32,
            elements: [VertexElement]
        ) throws {
            guard !elements.isEmpty else {
                storedElements = nil
                storedStride = 0
                super.init(storage: nil, device: nil)
                return
            }
            storedElements = elements
            storedStride = vertexStride
            super.init(storage: nil, device: nil)
            try VertexElementValidator.validate(
                vertexStride: vertexStride, elements: elements)
        }

        /// `VertexDeclaration..ctor(VertexElement[] elements)`.
        ///
        /// The stride is computed from the elements and then validated, so an
        /// element list whose maximum end offset is not a multiple of four is
        /// refused by the same alignment message even though the caller never
        /// supplied a stride.
        public convenience init(elements: [VertexElement]) throws {
            try self.init(
                vertexStride: VertexElementValidator.vertexStride(elements),
                elements: elements)
        }

        /// `VertexDeclaration.VertexStride`.
        ///
        /// `ldfld _vertexStride; ret` — a bare field read with no failure
        /// path, so the Swift reader does not throw.
        public var VertexStride: Int32 { storedStride }

        /// `VertexDeclaration.GetVertexElements()`.
        ///
        /// Returns a **copy**, so a caller mutating the result does not change
        /// the declaration — Swift's value-typed `Array` gives that for free
        /// where the CLR needs `Array.Clone()`.
        ///
        /// It throws where the CLR's own `callvirt` would: the whole body is
        /// `ldfld _elements; callvirt Array::Clone()`, and `_elements` is null
        /// exactly when the constructor accepted an empty array, so
        /// `NullReferenceException` is reachable. The pinned fallibility record
        /// says `IL_NO_FAILURE_PATH` because the analyser does not treat a
        /// `callvirt` on a possibly-null field as a failure path; that record
        /// is wrong and nothing depends on it, so the IL is followed instead.
        public func GetVertexElements() throws -> [VertexElement] {
            guard let storedElements else { throw CNANullReferenceException() }
            return storedElements
        }

        /// `Dispose(Boolean)`.
        ///
        /// XNA's override runs `~VertexDeclaration()` or `!VertexDeclaration()`
        /// and then `base.Dispose(disposing)`; `~VertexDeclaration()` calls
        /// `!VertexDeclaration()`, whose whole body is `Unbind()` — internal
        /// device-binding bookkeeping with no Swift counterpart. So this
        /// reduces to the base call, and that is shown rather than assumed.
        open override func Dispose(_ disposing: Bool) throws {
            try super.Dispose(disposing)
        }
    }
}
