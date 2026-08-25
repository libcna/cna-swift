# XNA to Swift missing-type inventory

Generated from the compiler Symbol Graph and the pinned XNA 4.0 Windows runtime contract.
Normal strict status is intentionally red.

```text
REFERENCE_TYPES=257
REFERENCE_MEMBERS=2964
EXPECTED_SWIFT_TYPES=257
EXPECTED_SWIFT_MEMBERS=2887
TARGET_TYPES=98
TARGET_MEMBERS=1560
TOTAL_DIAGNOSTICS=310
COMPLETE_TYPES=93
PARTIAL_TYPES=5
MISSING_TYPES=159
MISSING_TYPE=159
MISSING_MEMBER=131
UNEXPECTED_TYPE=0
UNEXPECTED_MEMBER=0
TYPE_KIND_MISMATCH=0
BASE_MAPPING_MISMATCH=2
INTERFACE_MAPPING_MISMATCH=1
FIELD_MAPPING_MISMATCH=0
PROPERTY_MAPPING_MISMATCH=1
METHOD_SIGNATURE_MAPPING_MISMATCH=0
PARAMETER_MAPPING_MISMATCH=0
RETURN_MAPPING_MISMATCH=0
OVERLOAD_MAPPING_MISMATCH=16
GENERIC_MAPPING_MISMATCH=0
ENUM_VALUE_MISMATCH=0
FLAGS_MAPPING_MISMATCH=0
EVENT_MAPPING_MISMATCH=0
OPERATOR_MAPPING_MISMATCH=0
REF_OUT_MAPPING_MISMATCH=0
LANGUAGE_MAPPING_MISMATCH=0
INTERNAL_TYPE_LEAK=0
RAW_HANDLE_LEAK=0
PUBLIC_NATIVE_FFI_LEAK=0
UNMEASURED_STRUCTURAL_CATEGORY=0
ALLOWLIST_ENTRIES=0
APPLIED_ALLOWLIST_ENTRIES=0
LANGUAGE_PROJECTION_EXCLUSIONS=114
ENUM_STORAGE_FIELD_EXCLUSIONS=49
FINALIZER_LANGUAGE_MAPPINGS=28
NAMESPACE_MARKERS=8
INHERITED_MEMBER_PROJECTIONS=3
PROTOCOL_WITNESS_MEMBER_PROJECTIONS=26
ARRAY_MUTATION_MAPPINGS=19
COMPARABLE_INTERFACE_PROJECTIONS=1
COLLECTION_INTERFACE_PROJECTIONS=1
ENUMERATOR_SUPPORT_PROJECTIONS=9
INDEXED_PROPERTY_ACCESSOR_PROJECTIONS=4
GLOBAL_OPTIONAL_OPERATOR_PROJECTIONS=2
NONPUBLIC_CONSTRUCTION_PROJECTIONS=4
```

## Complete types

- `Microsoft.Xna.Framework.Audio.AudioChannels`
- `Microsoft.Xna.Framework.Audio.SoundState`
- `Microsoft.Xna.Framework.BoundingBox`
- `Microsoft.Xna.Framework.BoundingFrustum`
- `Microsoft.Xna.Framework.BoundingSphere`
- `Microsoft.Xna.Framework.Color`
- `Microsoft.Xna.Framework.ContainmentType`
- `Microsoft.Xna.Framework.Curve`
- `Microsoft.Xna.Framework.CurveContinuity`
- `Microsoft.Xna.Framework.CurveKey`
- `Microsoft.Xna.Framework.CurveKeyCollection`
- `Microsoft.Xna.Framework.CurveLoopType`
- `Microsoft.Xna.Framework.CurveTangent`
- `Microsoft.Xna.Framework.DisplayOrientation`
- `Microsoft.Xna.Framework.GameTime`
- `Microsoft.Xna.Framework.Graphics.Blend`
- `Microsoft.Xna.Framework.Graphics.BlendFunction`
- `Microsoft.Xna.Framework.Graphics.BufferUsage`
- `Microsoft.Xna.Framework.Graphics.ClearOptions`
- `Microsoft.Xna.Framework.Graphics.ColorWriteChannels`
- `Microsoft.Xna.Framework.Graphics.CompareFunction`
- `Microsoft.Xna.Framework.Graphics.CubeMapFace`
- `Microsoft.Xna.Framework.Graphics.CullMode`
- `Microsoft.Xna.Framework.Graphics.DepthFormat`
- `Microsoft.Xna.Framework.Graphics.DisplayMode`
- `Microsoft.Xna.Framework.Graphics.EffectParameterClass`
- `Microsoft.Xna.Framework.Graphics.EffectParameterType`
- `Microsoft.Xna.Framework.Graphics.FillMode`
- `Microsoft.Xna.Framework.Graphics.GraphicsDeviceStatus`
- `Microsoft.Xna.Framework.Graphics.GraphicsProfile`
- `Microsoft.Xna.Framework.Graphics.IEffectFog`
- `Microsoft.Xna.Framework.Graphics.IEffectMatrices`
- `Microsoft.Xna.Framework.Graphics.IndexElementSize`
- `Microsoft.Xna.Framework.Graphics.PackedVector.Alpha8`
- `Microsoft.Xna.Framework.Graphics.PackedVector.Bgr565`
- `Microsoft.Xna.Framework.Graphics.PackedVector.Bgra4444`
- `Microsoft.Xna.Framework.Graphics.PackedVector.Bgra5551`
- `Microsoft.Xna.Framework.Graphics.PackedVector.Byte4`
- `Microsoft.Xna.Framework.Graphics.PackedVector.HalfSingle`
- `Microsoft.Xna.Framework.Graphics.PackedVector.HalfVector2`
- `Microsoft.Xna.Framework.Graphics.PackedVector.HalfVector4`
- `Microsoft.Xna.Framework.Graphics.PackedVector.IPackedVector`
- `Microsoft.Xna.Framework.Graphics.PackedVector.IPackedVectorOfT`
- `Microsoft.Xna.Framework.Graphics.PackedVector.NormalizedByte2`
- `Microsoft.Xna.Framework.Graphics.PackedVector.NormalizedByte4`
- `Microsoft.Xna.Framework.Graphics.PackedVector.NormalizedShort2`
- `Microsoft.Xna.Framework.Graphics.PackedVector.NormalizedShort4`
- `Microsoft.Xna.Framework.Graphics.PackedVector.Rg32`
- `Microsoft.Xna.Framework.Graphics.PackedVector.Rgba1010102`
- `Microsoft.Xna.Framework.Graphics.PackedVector.Rgba64`
- `Microsoft.Xna.Framework.Graphics.PackedVector.Short2`
- `Microsoft.Xna.Framework.Graphics.PackedVector.Short4`
- `Microsoft.Xna.Framework.Graphics.PresentInterval`
- `Microsoft.Xna.Framework.Graphics.PrimitiveType`
- `Microsoft.Xna.Framework.Graphics.RenderTargetUsage`
- `Microsoft.Xna.Framework.Graphics.SetDataOptions`
- `Microsoft.Xna.Framework.Graphics.SpriteEffects`
- `Microsoft.Xna.Framework.Graphics.SpriteSortMode`
- `Microsoft.Xna.Framework.Graphics.StencilOperation`
- `Microsoft.Xna.Framework.Graphics.SurfaceFormat`
- `Microsoft.Xna.Framework.Graphics.TextureAddressMode`
- `Microsoft.Xna.Framework.Graphics.TextureFilter`
- `Microsoft.Xna.Framework.Graphics.VertexElement`
- `Microsoft.Xna.Framework.Graphics.VertexElementFormat`
- `Microsoft.Xna.Framework.Graphics.VertexElementUsage`
- `Microsoft.Xna.Framework.Graphics.Viewport`
- `Microsoft.Xna.Framework.Input.ButtonState`
- `Microsoft.Xna.Framework.Input.Buttons`
- `Microsoft.Xna.Framework.Input.GamePad`
- `Microsoft.Xna.Framework.Input.GamePadButtons`
- `Microsoft.Xna.Framework.Input.GamePadCapabilities`
- `Microsoft.Xna.Framework.Input.GamePadDPad`
- `Microsoft.Xna.Framework.Input.GamePadDeadZone`
- `Microsoft.Xna.Framework.Input.GamePadState`
- `Microsoft.Xna.Framework.Input.GamePadThumbSticks`
- `Microsoft.Xna.Framework.Input.GamePadTriggers`
- `Microsoft.Xna.Framework.Input.GamePadType`
- `Microsoft.Xna.Framework.Input.KeyState`
- `Microsoft.Xna.Framework.Input.Keyboard`
- `Microsoft.Xna.Framework.Input.KeyboardState`
- `Microsoft.Xna.Framework.Input.Keys`
- `Microsoft.Xna.Framework.MathHelper`
- `Microsoft.Xna.Framework.Matrix`
- `Microsoft.Xna.Framework.Plane`
- `Microsoft.Xna.Framework.PlaneIntersectionType`
- `Microsoft.Xna.Framework.PlayerIndex`
- `Microsoft.Xna.Framework.Point`
- `Microsoft.Xna.Framework.Quaternion`
- `Microsoft.Xna.Framework.Ray`
- `Microsoft.Xna.Framework.Rectangle`
- `Microsoft.Xna.Framework.Vector2`
- `Microsoft.Xna.Framework.Vector3`
- `Microsoft.Xna.Framework.Vector4`

## Partial types and exact diagnostics

### `Microsoft.Xna.Framework.Game`

Expected members: 37; emitted members: 16.

- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.Tick()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.SuppressDraw()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.ResetElapsedTime()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.OnActivated(_:Any?,args:CNAEventArgs)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.OnDeactivated(_:Any?,args:CNAEventArgs)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.Dispose(_:Bool)`: mapped member is absent
- `OVERLOAD_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Game.Dispose(_:Bool)`: required overload is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.ShowMissingRequirementMessage(_:System.Exception)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.LaunchParameters()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.Components()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.Services()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.InactiveSleepTime()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.IsMouseVisible()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.TargetElapsedTime()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.IsFixedTimeStep()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.Window()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.IsActive()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.Content()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.Activated()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.Deactivated()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.Exiting()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Game.Disposed()`: mapped member is absent

### `Microsoft.Xna.Framework.Graphics.GraphicsDevice`

Expected members: 56; emitted members: 2.

- `PROPERTY_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.Viewport()`: expected mutable=True, found mutable=False
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice..ctor(adapter:Microsoft.Xna.Framework.Graphics.GraphicsAdapter,graphicsProfile:Microsoft.Xna.Framework.Graphics.GraphicsProfile,presentationParameters:Microsoft.Xna.Framework.Graphics.PresentationParameters)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.Present(_:Microsoft.Xna.Framework.Rectangle?,destinationRectangle:Microsoft.Xna.Framework.Rectangle?,overrideWindowHandle:Int)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.Present()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.Reset()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.Reset(_:Microsoft.Xna.Framework.Graphics.PresentationParameters)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.Reset(_:Microsoft.Xna.Framework.Graphics.PresentationParameters,graphicsAdapter:Microsoft.Xna.Framework.Graphics.GraphicsAdapter)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.DrawPrimitives(_:Microsoft.Xna.Framework.Graphics.PrimitiveType,startVertex:Int32,primitiveCount:Int32)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.DrawIndexedPrimitives(_:Microsoft.Xna.Framework.Graphics.PrimitiveType,baseVertex:Int32,minVertexIndex:Int32,numVertices:Int32,startIndex:Int32,primitiveCount:Int32)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.DrawInstancedPrimitives(_:Microsoft.Xna.Framework.Graphics.PrimitiveType,baseVertex:Int32,minVertexIndex:Int32,numVertices:Int32,startIndex:Int32,primitiveCount:Int32,instanceCount:Int32)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.DrawUserIndexedPrimitives(_:Microsoft.Xna.Framework.Graphics.PrimitiveType,vertexData:[!!0],vertexOffset:Int32,numVertices:Int32,indexData:[Int32],indexOffset:Int32,primitiveCount:Int32)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.DrawUserIndexedPrimitives(_:Microsoft.Xna.Framework.Graphics.PrimitiveType,vertexData:[!!0],vertexOffset:Int32,numVertices:Int32,indexData:[Int16],indexOffset:Int32,primitiveCount:Int32)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.DrawUserIndexedPrimitives(_:Microsoft.Xna.Framework.Graphics.PrimitiveType,vertexData:[!!0],vertexOffset:Int32,numVertices:Int32,indexData:[Int32],indexOffset:Int32,primitiveCount:Int32,vertexDeclaration:Microsoft.Xna.Framework.Graphics.VertexDeclaration)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.DrawUserIndexedPrimitives(_:Microsoft.Xna.Framework.Graphics.PrimitiveType,vertexData:[!!0],vertexOffset:Int32,numVertices:Int32,indexData:[Int16],indexOffset:Int32,primitiveCount:Int32,vertexDeclaration:Microsoft.Xna.Framework.Graphics.VertexDeclaration)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.DrawUserPrimitives(_:Microsoft.Xna.Framework.Graphics.PrimitiveType,vertexData:[!!0],vertexOffset:Int32,primitiveCount:Int32)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.DrawUserPrimitives(_:Microsoft.Xna.Framework.Graphics.PrimitiveType,vertexData:[!!0],vertexOffset:Int32,primitiveCount:Int32,vertexDeclaration:Microsoft.Xna.Framework.Graphics.VertexDeclaration)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.Clear(_:Microsoft.Xna.Framework.Graphics.ClearOptions,color:Microsoft.Xna.Framework.Vector4,depth:Float,stencil:Int32)`: mapped member is absent
- `OVERLOAD_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.Clear(_:Microsoft.Xna.Framework.Graphics.ClearOptions,color:Microsoft.Xna.Framework.Vector4,depth:Float,stencil:Int32)`: required overload is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.Clear(_:Microsoft.Xna.Framework.Graphics.ClearOptions,color:Microsoft.Xna.Framework.Color,depth:Float,stencil:Int32)`: mapped member is absent
- `OVERLOAD_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.Clear(_:Microsoft.Xna.Framework.Graphics.ClearOptions,color:Microsoft.Xna.Framework.Color,depth:Float,stencil:Int32)`: required overload is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.SetRenderTargets(_:[Microsoft.Xna.Framework.Graphics.RenderTargetBinding])`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.SetRenderTarget(_:Microsoft.Xna.Framework.Graphics.RenderTargetCube,cubeMapFace:Microsoft.Xna.Framework.Graphics.CubeMapFace)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.SetRenderTarget(_:Microsoft.Xna.Framework.Graphics.RenderTarget2D)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.GetRenderTargets()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.GetBackBufferData(_:Microsoft.Xna.Framework.Rectangle?,data:[!!0],startIndex:Int32,elementCount:Int32)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.GetBackBufferData(_:[!!0],startIndex:Int32,elementCount:Int32)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.GetBackBufferData(_:[!!0])`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.GetVertexBuffers()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.SetVertexBuffer(_:Microsoft.Xna.Framework.Graphics.VertexBuffer,vertexOffset:Int32)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.SetVertexBuffer(_:Microsoft.Xna.Framework.Graphics.VertexBuffer)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.SetVertexBuffers(_:[Microsoft.Xna.Framework.Graphics.VertexBufferBinding])`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.Dispose(_:Bool)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.Dispose()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.IsDisposed()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.ScissorRectangle()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.Indices()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.DisplayMode()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.GraphicsDeviceStatus()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.GraphicsProfile()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.Adapter()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.PresentationParameters()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.RasterizerState()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.ReferenceStencil()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.DepthStencilState()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.MultiSampleMask()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.BlendFactor()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.BlendState()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.VertexTextures()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.Textures()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.VertexSamplerStates()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.SamplerStates()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.Disposing()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.ResourceDestroyed()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.ResourceCreated()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.DeviceLost()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.DeviceReset()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.GraphicsDevice.DeviceResetting()`: mapped member is absent

### `Microsoft.Xna.Framework.Graphics.SpriteBatch`

Expected members: 21; emitted members: 6.

- `BASE_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Graphics.SpriteBatch`: expected base Microsoft.Xna.Framework.Graphics.GraphicsResource, found None
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Dispose(_:Bool)`: mapped overload is absent
- `OVERLOAD_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Dispose(_:Bool)`: required overload is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Begin(_:Microsoft.Xna.Framework.Graphics.SpriteSortMode,blendState:Microsoft.Xna.Framework.Graphics.BlendState)`: mapped member is absent
- `OVERLOAD_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Begin(_:Microsoft.Xna.Framework.Graphics.SpriteSortMode,blendState:Microsoft.Xna.Framework.Graphics.BlendState)`: required overload is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Begin(_:Microsoft.Xna.Framework.Graphics.SpriteSortMode,blendState:Microsoft.Xna.Framework.Graphics.BlendState,samplerState:Microsoft.Xna.Framework.Graphics.SamplerState,depthStencilState:Microsoft.Xna.Framework.Graphics.DepthStencilState,rasterizerState:Microsoft.Xna.Framework.Graphics.RasterizerState)`: mapped member is absent
- `OVERLOAD_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Begin(_:Microsoft.Xna.Framework.Graphics.SpriteSortMode,blendState:Microsoft.Xna.Framework.Graphics.BlendState,samplerState:Microsoft.Xna.Framework.Graphics.SamplerState,depthStencilState:Microsoft.Xna.Framework.Graphics.DepthStencilState,rasterizerState:Microsoft.Xna.Framework.Graphics.RasterizerState)`: required overload is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Begin(_:Microsoft.Xna.Framework.Graphics.SpriteSortMode,blendState:Microsoft.Xna.Framework.Graphics.BlendState,samplerState:Microsoft.Xna.Framework.Graphics.SamplerState,depthStencilState:Microsoft.Xna.Framework.Graphics.DepthStencilState,rasterizerState:Microsoft.Xna.Framework.Graphics.RasterizerState,effect:Microsoft.Xna.Framework.Graphics.Effect)`: mapped member is absent
- `OVERLOAD_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Begin(_:Microsoft.Xna.Framework.Graphics.SpriteSortMode,blendState:Microsoft.Xna.Framework.Graphics.BlendState,samplerState:Microsoft.Xna.Framework.Graphics.SamplerState,depthStencilState:Microsoft.Xna.Framework.Graphics.DepthStencilState,rasterizerState:Microsoft.Xna.Framework.Graphics.RasterizerState,effect:Microsoft.Xna.Framework.Graphics.Effect)`: required overload is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Begin(_:Microsoft.Xna.Framework.Graphics.SpriteSortMode,blendState:Microsoft.Xna.Framework.Graphics.BlendState,samplerState:Microsoft.Xna.Framework.Graphics.SamplerState,depthStencilState:Microsoft.Xna.Framework.Graphics.DepthStencilState,rasterizerState:Microsoft.Xna.Framework.Graphics.RasterizerState,effect:Microsoft.Xna.Framework.Graphics.Effect,transformMatrix:Microsoft.Xna.Framework.Matrix)`: mapped member is absent
- `OVERLOAD_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Begin(_:Microsoft.Xna.Framework.Graphics.SpriteSortMode,blendState:Microsoft.Xna.Framework.Graphics.BlendState,samplerState:Microsoft.Xna.Framework.Graphics.SamplerState,depthStencilState:Microsoft.Xna.Framework.Graphics.DepthStencilState,rasterizerState:Microsoft.Xna.Framework.Graphics.RasterizerState,effect:Microsoft.Xna.Framework.Graphics.Effect,transformMatrix:Microsoft.Xna.Framework.Matrix)`: required overload is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Draw(_:Microsoft.Xna.Framework.Graphics.Texture2D,position:Microsoft.Xna.Framework.Vector2,sourceRectangle:Microsoft.Xna.Framework.Rectangle?,color:Microsoft.Xna.Framework.Color)`: mapped member is absent
- `OVERLOAD_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Draw(_:Microsoft.Xna.Framework.Graphics.Texture2D,position:Microsoft.Xna.Framework.Vector2,sourceRectangle:Microsoft.Xna.Framework.Rectangle?,color:Microsoft.Xna.Framework.Color)`: required overload is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Draw(_:Microsoft.Xna.Framework.Graphics.Texture2D,position:Microsoft.Xna.Framework.Vector2,sourceRectangle:Microsoft.Xna.Framework.Rectangle?,color:Microsoft.Xna.Framework.Color,rotation:Float,origin:Microsoft.Xna.Framework.Vector2,scale:Microsoft.Xna.Framework.Vector2,effects:Microsoft.Xna.Framework.Graphics.SpriteEffects,layerDepth:Float)`: mapped member is absent
- `OVERLOAD_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Draw(_:Microsoft.Xna.Framework.Graphics.Texture2D,position:Microsoft.Xna.Framework.Vector2,sourceRectangle:Microsoft.Xna.Framework.Rectangle?,color:Microsoft.Xna.Framework.Color,rotation:Float,origin:Microsoft.Xna.Framework.Vector2,scale:Microsoft.Xna.Framework.Vector2,effects:Microsoft.Xna.Framework.Graphics.SpriteEffects,layerDepth:Float)`: required overload is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Draw(_:Microsoft.Xna.Framework.Graphics.Texture2D,destinationRectangle:Microsoft.Xna.Framework.Rectangle,color:Microsoft.Xna.Framework.Color)`: mapped member is absent
- `OVERLOAD_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Draw(_:Microsoft.Xna.Framework.Graphics.Texture2D,destinationRectangle:Microsoft.Xna.Framework.Rectangle,color:Microsoft.Xna.Framework.Color)`: required overload is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Draw(_:Microsoft.Xna.Framework.Graphics.Texture2D,destinationRectangle:Microsoft.Xna.Framework.Rectangle,sourceRectangle:Microsoft.Xna.Framework.Rectangle?,color:Microsoft.Xna.Framework.Color)`: mapped member is absent
- `OVERLOAD_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Draw(_:Microsoft.Xna.Framework.Graphics.Texture2D,destinationRectangle:Microsoft.Xna.Framework.Rectangle,sourceRectangle:Microsoft.Xna.Framework.Rectangle?,color:Microsoft.Xna.Framework.Color)`: required overload is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Draw(_:Microsoft.Xna.Framework.Graphics.Texture2D,destinationRectangle:Microsoft.Xna.Framework.Rectangle,sourceRectangle:Microsoft.Xna.Framework.Rectangle?,color:Microsoft.Xna.Framework.Color,rotation:Float,origin:Microsoft.Xna.Framework.Vector2,effects:Microsoft.Xna.Framework.Graphics.SpriteEffects,layerDepth:Float)`: mapped member is absent
- `OVERLOAD_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.Draw(_:Microsoft.Xna.Framework.Graphics.Texture2D,destinationRectangle:Microsoft.Xna.Framework.Rectangle,sourceRectangle:Microsoft.Xna.Framework.Rectangle?,color:Microsoft.Xna.Framework.Color,rotation:Float,origin:Microsoft.Xna.Framework.Vector2,effects:Microsoft.Xna.Framework.Graphics.SpriteEffects,layerDepth:Float)`: required overload is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.DrawString(_:Microsoft.Xna.Framework.Graphics.SpriteFont,text:String,position:Microsoft.Xna.Framework.Vector2,color:Microsoft.Xna.Framework.Color)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.DrawString(_:Microsoft.Xna.Framework.Graphics.SpriteFont,text:System.Text.StringBuilder,position:Microsoft.Xna.Framework.Vector2,color:Microsoft.Xna.Framework.Color)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.DrawString(_:Microsoft.Xna.Framework.Graphics.SpriteFont,text:String,position:Microsoft.Xna.Framework.Vector2,color:Microsoft.Xna.Framework.Color,rotation:Float,origin:Microsoft.Xna.Framework.Vector2,scale:Float,effects:Microsoft.Xna.Framework.Graphics.SpriteEffects,layerDepth:Float)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.DrawString(_:Microsoft.Xna.Framework.Graphics.SpriteFont,text:System.Text.StringBuilder,position:Microsoft.Xna.Framework.Vector2,color:Microsoft.Xna.Framework.Color,rotation:Float,origin:Microsoft.Xna.Framework.Vector2,scale:Float,effects:Microsoft.Xna.Framework.Graphics.SpriteEffects,layerDepth:Float)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.DrawString(_:Microsoft.Xna.Framework.Graphics.SpriteFont,text:String,position:Microsoft.Xna.Framework.Vector2,color:Microsoft.Xna.Framework.Color,rotation:Float,origin:Microsoft.Xna.Framework.Vector2,scale:Microsoft.Xna.Framework.Vector2,effects:Microsoft.Xna.Framework.Graphics.SpriteEffects,layerDepth:Float)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.SpriteBatch.DrawString(_:Microsoft.Xna.Framework.Graphics.SpriteFont,text:System.Text.StringBuilder,position:Microsoft.Xna.Framework.Vector2,color:Microsoft.Xna.Framework.Color,rotation:Float,origin:Microsoft.Xna.Framework.Vector2,scale:Microsoft.Xna.Framework.Vector2,effects:Microsoft.Xna.Framework.Graphics.SpriteEffects,layerDepth:Float)`: mapped member is absent

### `Microsoft.Xna.Framework.Graphics.Texture2D`

Expected members: 16; emitted members: 4.

- `BASE_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Graphics.Texture2D`: expected base Microsoft.Xna.Framework.Graphics.Texture, found None
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.Texture2D..ctor(graphicsDevice:Microsoft.Xna.Framework.Graphics.GraphicsDevice,width:Int32,height:Int32)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.Texture2D..ctor(graphicsDevice:Microsoft.Xna.Framework.Graphics.GraphicsDevice,width:Int32,height:Int32,mipMap:Bool,format:Microsoft.Xna.Framework.Graphics.SurfaceFormat)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.Texture2D.FromStream(_:Microsoft.Xna.Framework.Graphics.GraphicsDevice,stream:Foundation.InputStream,width:Int32,height:Int32,zoom:Bool)`: mapped member is absent
- `OVERLOAD_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Graphics.Texture2D.FromStream(_:Microsoft.Xna.Framework.Graphics.GraphicsDevice,stream:Foundation.InputStream,width:Int32,height:Int32,zoom:Bool)`: required overload is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.Texture2D.SaveAsJpeg(_:Foundation.InputStream,width:Int32,height:Int32)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.Texture2D.SaveAsPng(_:Foundation.InputStream,width:Int32,height:Int32)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.Texture2D.SetData(_:[!!0])`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.Texture2D.SetData(_:[!!0],startIndex:Int32,elementCount:Int32)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.Texture2D.SetData(_:Int32,rect:Microsoft.Xna.Framework.Rectangle?,data:[!!0],startIndex:Int32,elementCount:Int32)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.Texture2D.GetData(_:[!!0])`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.Texture2D.GetData(_:[!!0],startIndex:Int32,elementCount:Int32)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.Texture2D.GetData(_:Int32,rect:Microsoft.Xna.Framework.Rectangle?,data:[!!0],startIndex:Int32,elementCount:Int32)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.Texture2D.Dispose(_:Bool)`: mapped overload is absent
- `OVERLOAD_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.Graphics.Texture2D.Dispose(_:Bool)`: required overload is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.Graphics.Texture2D.Bounds()`: mapped member is absent

### `Microsoft.Xna.Framework.GraphicsDeviceManager`

Expected members: 30; emitted members: 4.

- `INTERFACE_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.GraphicsDeviceManager`: missing protocols ['Microsoft.Xna.Framework.Graphics.IGraphicsDeviceService', 'Microsoft.Xna.Framework.IGraphicsDeviceManager']
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.ToggleFullScreen()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.FindBestDevice(_:Bool)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.CanResetDevice(_:Microsoft.Xna.Framework.GraphicsDeviceInformation)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.RankDevices(_:System.Collections.Generic.List<Microsoft.Xna.Framework.GraphicsDeviceInformation>)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.OnDeviceCreated(_:Any?,args:CNAEventArgs)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.OnDeviceDisposing(_:Any?,args:CNAEventArgs)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.OnDeviceReset(_:Any?,args:CNAEventArgs)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.OnDeviceResetting(_:Any?,args:CNAEventArgs)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.Dispose(_:Bool)`: mapped overload is absent
- `OVERLOAD_MAPPING_MISMATCH` — `Microsoft.Xna.Framework.GraphicsDeviceManager.Dispose(_:Bool)`: required overload is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.OnPreparingDeviceSettings(_:Any?,args:Microsoft.Xna.Framework.PreparingDeviceSettingsEventArgs)`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.GraphicsProfile()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.PreferredDepthStencilFormat()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.PreferredBackBufferFormat()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.PreferredBackBufferWidth()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.PreferredBackBufferHeight()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.IsFullScreen()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.SynchronizeWithVerticalRetrace()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.PreferMultiSampling()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.SupportedOrientations()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.DeviceCreated()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.DeviceResetting()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.DeviceReset()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.DeviceDisposing()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.PreparingDeviceSettings()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.Disposed()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.DefaultBackBufferWidth()`: mapped member is absent
- `MISSING_MEMBER` — `Microsoft.Xna.Framework.GraphicsDeviceManager.DefaultBackBufferHeight()`: mapped member is absent

## Missing types

- `Microsoft.Xna.Framework.Audio.AudioCategory`
- `Microsoft.Xna.Framework.Audio.AudioEmitter`
- `Microsoft.Xna.Framework.Audio.AudioEngine`
- `Microsoft.Xna.Framework.Audio.AudioListener`
- `Microsoft.Xna.Framework.Audio.AudioStopOptions`
- `Microsoft.Xna.Framework.Audio.Cue`
- `Microsoft.Xna.Framework.Audio.DynamicSoundEffectInstance`
- `Microsoft.Xna.Framework.Audio.InstancePlayLimitException`
- `Microsoft.Xna.Framework.Audio.Microphone`
- `Microsoft.Xna.Framework.Audio.MicrophoneState`
- `Microsoft.Xna.Framework.Audio.NoAudioHardwareException`
- `Microsoft.Xna.Framework.Audio.NoMicrophoneConnectedException`
- `Microsoft.Xna.Framework.Audio.RendererDetail`
- `Microsoft.Xna.Framework.Audio.SoundBank`
- `Microsoft.Xna.Framework.Audio.SoundEffect`
- `Microsoft.Xna.Framework.Audio.SoundEffectInstance`
- `Microsoft.Xna.Framework.Audio.WaveBank`
- `Microsoft.Xna.Framework.Content.ContentLoadException`
- `Microsoft.Xna.Framework.Content.ContentManager`
- `Microsoft.Xna.Framework.Content.ContentReader`
- `Microsoft.Xna.Framework.Content.ContentSerializerAttribute`
- `Microsoft.Xna.Framework.Content.ContentSerializerCollectionItemNameAttribute`
- `Microsoft.Xna.Framework.Content.ContentSerializerIgnoreAttribute`
- `Microsoft.Xna.Framework.Content.ContentSerializerRuntimeTypeAttribute`
- `Microsoft.Xna.Framework.Content.ContentSerializerTypeVersionAttribute`
- `Microsoft.Xna.Framework.Content.ContentTypeReader`
- `Microsoft.Xna.Framework.Content.ContentTypeReaderManager`
- `Microsoft.Xna.Framework.Content.ContentTypeReaderOfT`
- `Microsoft.Xna.Framework.Content.ResourceContentManager`
- `Microsoft.Xna.Framework.Design.BoundingBoxConverter`
- `Microsoft.Xna.Framework.Design.BoundingSphereConverter`
- `Microsoft.Xna.Framework.Design.ColorConverter`
- `Microsoft.Xna.Framework.Design.MathTypeConverter`
- `Microsoft.Xna.Framework.Design.MatrixConverter`
- `Microsoft.Xna.Framework.Design.PlaneConverter`
- `Microsoft.Xna.Framework.Design.PointConverter`
- `Microsoft.Xna.Framework.Design.QuaternionConverter`
- `Microsoft.Xna.Framework.Design.RayConverter`
- `Microsoft.Xna.Framework.Design.RectangleConverter`
- `Microsoft.Xna.Framework.Design.Vector2Converter`
- `Microsoft.Xna.Framework.Design.Vector3Converter`
- `Microsoft.Xna.Framework.Design.Vector4Converter`
- `Microsoft.Xna.Framework.DrawableGameComponent`
- `Microsoft.Xna.Framework.FrameworkDispatcher`
- `Microsoft.Xna.Framework.GameComponent`
- `Microsoft.Xna.Framework.GameComponentCollection`
- `Microsoft.Xna.Framework.GameComponentCollectionEventArgs`
- `Microsoft.Xna.Framework.GameServiceContainer`
- `Microsoft.Xna.Framework.GameWindow`
- `Microsoft.Xna.Framework.GamerServices.GamerServicesComponent`
- `Microsoft.Xna.Framework.Graphics.AlphaTestEffect`
- `Microsoft.Xna.Framework.Graphics.BasicEffect`
- `Microsoft.Xna.Framework.Graphics.BlendState`
- `Microsoft.Xna.Framework.Graphics.DepthStencilState`
- `Microsoft.Xna.Framework.Graphics.DeviceLostException`
- `Microsoft.Xna.Framework.Graphics.DeviceNotResetException`
- `Microsoft.Xna.Framework.Graphics.DirectionalLight`
- `Microsoft.Xna.Framework.Graphics.DisplayModeCollection`
- `Microsoft.Xna.Framework.Graphics.DualTextureEffect`
- `Microsoft.Xna.Framework.Graphics.DynamicIndexBuffer`
- `Microsoft.Xna.Framework.Graphics.DynamicVertexBuffer`
- `Microsoft.Xna.Framework.Graphics.Effect`
- `Microsoft.Xna.Framework.Graphics.EffectAnnotation`
- `Microsoft.Xna.Framework.Graphics.EffectAnnotationCollection`
- `Microsoft.Xna.Framework.Graphics.EffectMaterial`
- `Microsoft.Xna.Framework.Graphics.EffectParameter`
- `Microsoft.Xna.Framework.Graphics.EffectParameterCollection`
- `Microsoft.Xna.Framework.Graphics.EffectPass`
- `Microsoft.Xna.Framework.Graphics.EffectPassCollection`
- `Microsoft.Xna.Framework.Graphics.EffectTechnique`
- `Microsoft.Xna.Framework.Graphics.EffectTechniqueCollection`
- `Microsoft.Xna.Framework.Graphics.EnvironmentMapEffect`
- `Microsoft.Xna.Framework.Graphics.GraphicsAdapter`
- `Microsoft.Xna.Framework.Graphics.GraphicsResource`
- `Microsoft.Xna.Framework.Graphics.IEffectLights`
- `Microsoft.Xna.Framework.Graphics.IGraphicsDeviceService`
- `Microsoft.Xna.Framework.Graphics.IVertexType`
- `Microsoft.Xna.Framework.Graphics.IndexBuffer`
- `Microsoft.Xna.Framework.Graphics.Model`
- `Microsoft.Xna.Framework.Graphics.ModelBone`
- `Microsoft.Xna.Framework.Graphics.ModelBoneCollection`
- `Microsoft.Xna.Framework.Graphics.ModelBoneCollection.Enumerator`
- `Microsoft.Xna.Framework.Graphics.ModelEffectCollection`
- `Microsoft.Xna.Framework.Graphics.ModelEffectCollection.Enumerator`
- `Microsoft.Xna.Framework.Graphics.ModelMesh`
- `Microsoft.Xna.Framework.Graphics.ModelMeshCollection`
- `Microsoft.Xna.Framework.Graphics.ModelMeshCollection.Enumerator`
- `Microsoft.Xna.Framework.Graphics.ModelMeshPart`
- `Microsoft.Xna.Framework.Graphics.ModelMeshPartCollection`
- `Microsoft.Xna.Framework.Graphics.ModelMeshPartCollection.Enumerator`
- `Microsoft.Xna.Framework.Graphics.NoSuitableGraphicsDeviceException`
- `Microsoft.Xna.Framework.Graphics.OcclusionQuery`
- `Microsoft.Xna.Framework.Graphics.PresentationParameters`
- `Microsoft.Xna.Framework.Graphics.RasterizerState`
- `Microsoft.Xna.Framework.Graphics.RenderTarget2D`
- `Microsoft.Xna.Framework.Graphics.RenderTargetBinding`
- `Microsoft.Xna.Framework.Graphics.RenderTargetCube`
- `Microsoft.Xna.Framework.Graphics.ResourceCreatedEventArgs`
- `Microsoft.Xna.Framework.Graphics.ResourceDestroyedEventArgs`
- `Microsoft.Xna.Framework.Graphics.SamplerState`
- `Microsoft.Xna.Framework.Graphics.SamplerStateCollection`
- `Microsoft.Xna.Framework.Graphics.SkinnedEffect`
- `Microsoft.Xna.Framework.Graphics.SpriteFont`
- `Microsoft.Xna.Framework.Graphics.Texture`
- `Microsoft.Xna.Framework.Graphics.Texture3D`
- `Microsoft.Xna.Framework.Graphics.TextureCollection`
- `Microsoft.Xna.Framework.Graphics.TextureCube`
- `Microsoft.Xna.Framework.Graphics.VertexBuffer`
- `Microsoft.Xna.Framework.Graphics.VertexBufferBinding`
- `Microsoft.Xna.Framework.Graphics.VertexDeclaration`
- `Microsoft.Xna.Framework.Graphics.VertexPositionColor`
- `Microsoft.Xna.Framework.Graphics.VertexPositionColorTexture`
- `Microsoft.Xna.Framework.Graphics.VertexPositionNormalTexture`
- `Microsoft.Xna.Framework.Graphics.VertexPositionTexture`
- `Microsoft.Xna.Framework.GraphicsDeviceInformation`
- `Microsoft.Xna.Framework.IDrawable`
- `Microsoft.Xna.Framework.IGameComponent`
- `Microsoft.Xna.Framework.IGraphicsDeviceManager`
- `Microsoft.Xna.Framework.IUpdateable`
- `Microsoft.Xna.Framework.Input.Mouse`
- `Microsoft.Xna.Framework.Input.MouseState`
- `Microsoft.Xna.Framework.Input.Touch.GestureSample`
- `Microsoft.Xna.Framework.Input.Touch.GestureType`
- `Microsoft.Xna.Framework.Input.Touch.TouchCollection`
- `Microsoft.Xna.Framework.Input.Touch.TouchCollection.Enumerator`
- `Microsoft.Xna.Framework.Input.Touch.TouchLocation`
- `Microsoft.Xna.Framework.Input.Touch.TouchLocationState`
- `Microsoft.Xna.Framework.Input.Touch.TouchPanel`
- `Microsoft.Xna.Framework.Input.Touch.TouchPanelCapabilities`
- `Microsoft.Xna.Framework.LaunchParameters`
- `Microsoft.Xna.Framework.Media.Album`
- `Microsoft.Xna.Framework.Media.AlbumCollection`
- `Microsoft.Xna.Framework.Media.Artist`
- `Microsoft.Xna.Framework.Media.ArtistCollection`
- `Microsoft.Xna.Framework.Media.Genre`
- `Microsoft.Xna.Framework.Media.GenreCollection`
- `Microsoft.Xna.Framework.Media.MediaLibrary`
- `Microsoft.Xna.Framework.Media.MediaPlayer`
- `Microsoft.Xna.Framework.Media.MediaQueue`
- `Microsoft.Xna.Framework.Media.MediaSource`
- `Microsoft.Xna.Framework.Media.MediaSourceType`
- `Microsoft.Xna.Framework.Media.MediaState`
- `Microsoft.Xna.Framework.Media.Picture`
- `Microsoft.Xna.Framework.Media.PictureAlbum`
- `Microsoft.Xna.Framework.Media.PictureAlbumCollection`
- `Microsoft.Xna.Framework.Media.PictureCollection`
- `Microsoft.Xna.Framework.Media.Playlist`
- `Microsoft.Xna.Framework.Media.PlaylistCollection`
- `Microsoft.Xna.Framework.Media.Song`
- `Microsoft.Xna.Framework.Media.SongCollection`
- `Microsoft.Xna.Framework.Media.Video`
- `Microsoft.Xna.Framework.Media.VideoPlayer`
- `Microsoft.Xna.Framework.Media.VideoSoundtrackType`
- `Microsoft.Xna.Framework.Media.VisualizationData`
- `Microsoft.Xna.Framework.PreparingDeviceSettingsEventArgs`
- `Microsoft.Xna.Framework.Storage.StorageContainer`
- `Microsoft.Xna.Framework.Storage.StorageDevice`
- `Microsoft.Xna.Framework.Storage.StorageDeviceNotConnectedException`
- `Microsoft.Xna.Framework.TitleContainer`
