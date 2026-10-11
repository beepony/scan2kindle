// Batch OCR helper using macOS Vision.
// Reads one image path per stdin line and writes one JSON object per line.
import AppKit
import Foundation
import Vision

setvbuf(stdout, nil, _IOLBF, 0)

func emit(_ obj: [String: Any]) {
    if let data = try? JSONSerialization.data(withJSONObject: obj),
       let line = String(data: data, encoding: .utf8) {
        print(line)
    }
}

var languages = ["zh-Hans", "en-US"]
let arguments = CommandLine.arguments
if let index = arguments.firstIndex(of: "--languages"), index + 1 < arguments.count {
    languages = arguments[index + 1].split(separator: ",").map { String($0).trimmingCharacters(in: .whitespaces) }
}

while let rawPath = readLine() {
    let path = rawPath.trimmingCharacters(in: .whitespacesAndNewlines)
    if path.isEmpty { continue }
    autoreleasepool {
        guard let image = NSImage(contentsOf: URL(fileURLWithPath: path)) else {
            emit(["path": path, "error": "cannot open image"])
            return
        }
        var rect = NSRect(origin: .zero, size: image.size)
        guard let cg = image.cgImage(forProposedRect: &rect, context: nil, hints: nil) else {
            emit(["path": path, "error": "cannot decode image"])
            return
        }
        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.recognitionLanguages = languages
        request.usesLanguageCorrection = true
        do {
            try VNImageRequestHandler(cgImage: cg, options: [:]).perform([request])
            let width = Double(cg.width)
            let height = Double(cg.height)
            var lines: [[String: Any]] = []
            for observation in request.results ?? [] {
                guard let candidate = observation.topCandidates(1).first else { continue }
                let box = observation.boundingBox
                // Convert Vision's normalized bottom-left box to top-left pixels.
                lines.append([
                    "text": candidate.string,
                    "conf": candidate.confidence,
                    "box": [
                        box.minX * width,
                        (1.0 - box.maxY) * height,
                        box.maxX * width,
                        (1.0 - box.minY) * height,
                    ],
                ])
            }
            emit(["path": path, "width": width, "height": height, "lines": lines])
        } catch {
            emit(["path": path, "error": error.localizedDescription])
        }
    }
}
