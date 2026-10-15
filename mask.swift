import Vision
import AppKit
import CoreImage

let url = URL(fileURLWithPath: CommandLine.arguments[1])
let out = URL(fileURLWithPath: CommandLine.arguments[2])
let handler = VNImageRequestHandler(url: url)
let req = VNGenerateForegroundInstanceMaskRequest()
try handler.perform([req])
guard let obs = req.results?.first else { print("no subject"); exit(1) }
let buf = try obs.generateScaledMaskForImage(forInstances: obs.allInstances, from: handler)
let ci = CIImage(cvPixelBuffer: buf)
let ctx = CIContext()
try ctx.writePNGRepresentation(of: ci, to: out, format: .L8, colorSpace: CGColorSpace(name: CGColorSpace.linearGray)!)
print("ok", CVPixelBufferGetWidth(buf), CVPixelBufferGetHeight(buf))
