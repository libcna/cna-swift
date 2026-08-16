import Foundation

public enum CnaError: Error {
    case nativeUnavailable
}

public struct GameTime {
    public var elapsed: TimeInterval
    public var total: TimeInterval
    
    public init(elapsed: TimeInterval = 0, total: TimeInterval = 0) {
        self.elapsed = elapsed
        self.total = total
    }
}

public protocol Game: AnyObject {
    func Initialize()
    func LoadContent()
    func Update(gameTime: GameTime)
    func Draw(gameTime: GameTime)
    func UnloadContent()
    func Exit()
}

public extension Game {
    func Initialize() {}
    func LoadContent() {}
    func Update(gameTime: GameTime) {}
    func Draw(gameTime: GameTime) {}
    func UnloadContent() {}
    func Exit() {
        Foundation.exit(0)
    }
}

public struct Vector2 {
    public var X: Float
    public var Y: Float
    
    public init(_ x: Float, _ y: Float) {
        self.X = x
        self.Y = y
    }
    
    public static var zero: Vector2 { Vector2(0, 0) }
}

public struct Vector3 {
    public var X: Float
    public var Y: Float
    public var Z: Float
    
    public init(_ x: Float, _ y: Float, _ z: Float) {
        self.X = x
        self.Y = y
        self.Z = z
    }
    
    public static var zero: Vector3 { Vector3(0, 0, 0) }
    public static var up: Vector3 { Vector3(0, 1, 0) }
}

public struct Matrix {
    public var m: [[Float]] // Simplified
    
    public init() {
        self.m = Array(repeating: Array(repeating: 0, count: 4), count: 4)
        for i in 0..<4 { self.m[i][i] = 1 }
    }
    
    public static var identity: Matrix { Matrix() }
    
    public static func createScale(_ scale: Float) -> Matrix {
        var result = Matrix()
        result.m[0][0] = scale
        result.m[1][1] = scale
        result.m[2][2] = scale
        return result
    }
    
    public static func createRotationX(_ radians: Float) -> Matrix { Matrix() }
    public static func createRotationY(_ radians: Float) -> Matrix { Matrix() }
    public static func createTranslation(_ x: Float, _ y: Float, _ z: Float) -> Matrix { Matrix() }
    public static func createLookAt(position: Vector3, target: Vector3, up: Vector3) -> Matrix { Matrix() }
    public static func createPerspectiveFieldOfView(fieldOfView: Float, aspectRatio: Float, nearPlaneDistance: Float, farPlaneDistance: Float) -> Matrix { Matrix() }
    
    public static func *(lhs: Matrix, rhs: Matrix) -> Matrix { Matrix() }
}

public struct Color {
    public var R: UInt8
    public var G: UInt8
    public var B: UInt8
    public var A: UInt8
    
    public init(_ r: UInt8, _ g: UInt8, _ b: UInt8, _ a: UInt8 = 255) {
        self.R = r
        self.G = g
        self.B = b
        self.A = a
    }
    
    public static var white: Color { Color(255, 255, 255) }
    public static var black: Color { Color(0, 0, 0) }
    public static var cornflowerBlue: Color { Color(100, 149, 237) }
}

public enum GraphicsCapability {
    case threeD
}

public struct Viewport {
    public var X: Int
    public var Y: Int
    public var Width: Int
    public var Height: Int
}

public class GraphicsDevice {
    public var Viewport: Viewport = Viewport(X: 0, Y: 0, Width: 1280, Height: 720)
    
    public func Clear(_ color: Color) {}
    public func SupportsCapability(_ capability: GraphicsCapability) -> Bool { true }
}

public class GraphicsDeviceManager {
    public var GraphicsDevice: GraphicsDevice = GraphicsDevice()
    
    public init(game: Game) {}
    public func ApplyChanges() {}
}

public class SpriteBatch {
    public init(device: GraphicsDevice) {}
    public func Begin() {}
    public func End() {}
    public func Draw(_ texture: Texture2D, _ position: Vector2, _ color: Color) {}
    public func DrawRect(_ texture: Texture2D, _ rect: [Float], _ color: Color) {}
}

public class Texture2D {
    public var Width: Int = 1
    public var Height: Int = 1
    public init() {}
}

public class ContentManager {
    public init() {}
    public func Load<T>(name: String) -> T? { nil }
}

public class BasicEffect {
    public var World: Matrix = .identity
    public var View: Matrix = .identity
    public var Projection: Matrix = .identity
    public var TextureEnabled: Bool = false
    public var Texture: Texture2D? = nil
    
    public init(device: GraphicsDevice) {}
    public func Apply() {}
}

public enum Keys {
    case escape
}

public struct KeyboardState {
    public func IsKeyDown(_ key: Keys) -> Bool { false }
}

public class Keyboard {
    public static func GetState() -> KeyboardState { KeyboardState() }
}

public func Run(game: Game) throws {
    // Native loop initialization would go here
    print("CNA: Starting Swift game loop...")
}
