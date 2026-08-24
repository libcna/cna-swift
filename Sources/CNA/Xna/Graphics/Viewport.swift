// SPDX-License-Identifier: MIT

import CNAShim

extension Microsoft.Xna.Framework.Graphics {
    public struct Viewport {
        public var X: Int32
        public var Y: Int32
        public var Width: Int32
        public var Height: Int32
        public var MinDepth: Float
        public var MaxDepth: Float

        internal init() {
            X = 0
            Y = 0
            Width = 0
            Height = 0
            MinDepth = 0
            MaxDepth = 1
        }

        public init(_ x: Int32, _ y: Int32, _ width: Int32, _ height: Int32) {
            X = x
            Y = y
            Width = width
            Height = height
            MinDepth = 0
            MaxDepth = 1
        }

        public init(_ bounds: Microsoft.Xna.Framework.Rectangle) {
            self.init(bounds.X, bounds.Y, bounds.Width, bounds.Height)
        }

        public var AspectRatio: Float {
            Width == 0 || Height == 0 ? 0 : Float(Width) / Float(Height)
        }

        public var Bounds: Microsoft.Xna.Framework.Rectangle {
            get { Microsoft.Xna.Framework.Rectangle(X, Y, Width, Height) }
            set { X = newValue.X; Y = newValue.Y; Width = newValue.Width; Height = newValue.Height }
        }

        public var TitleSafeArea: Microsoft.Xna.Framework.Rectangle { Bounds }

        internal init(native: CNASwift_Viewport) {
            X = native.x
            Y = native.y
            Width = native.width
            Height = native.height
            MinDepth = native.min_depth
            MaxDepth = native.max_depth
        }
    }
}
