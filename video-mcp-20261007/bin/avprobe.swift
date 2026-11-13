import Foundation
import AVFoundation
import CoreMedia
if CommandLine.arguments.contains("-version") { print("AVFoundation metadata adapter 1.0 (not ffprobe)"); exit(0) }
guard let input = CommandLine.arguments.last, input.hasPrefix("/") else { exit(2) }
let asset = AVURLAsset(url: URL(fileURLWithPath: input))
func fourcc(_ v: FourCharCode) -> String {
 let b:[UInt8] = [UInt8((v >> 24) & 255),UInt8((v >> 16) & 255),UInt8((v >> 8) & 255),UInt8(v & 255)]
 return String(bytes:b,encoding:.ascii) ?? "unknown"
}
var streams:[[String:Any]] = []
for t in asset.tracks {
 if t.mediaType != .video && t.mediaType != .audio { continue }
 let desc = t.formatDescriptions.first.map { $0 as! CMFormatDescription }
 let subtype = desc.map { fourcc(CMFormatDescriptionGetMediaSubType($0)) } ?? "unknown"
 let codec = ["hvc1":"hevc","hev1":"hevc","avc1":"h264","mp4a":"aac" ][subtype] ?? subtype.trimmingCharacters(in:.whitespaces)
 var row:[String:Any] = ["codec_type": t.mediaType == .video ? "video":"audio", "codec_name":codec]
 if t.mediaType == .video { row["width"] = Int(t.naturalSize.width); row["height"] = Int(t.naturalSize.height); row["avg_frame_rate"] = "\(t.nominalFrameRate)/1" }
 streams.append(row)
}
let duration = CMTimeGetSeconds(asset.duration)
guard duration.isFinite && duration > 0 && !streams.isEmpty else { fputs("AVFoundation could not read media\n",stderr); exit(1) }
let size = (try? FileManager.default.attributesOfItem(atPath:input)[.size] as? NSNumber)?.intValue ?? 0
let result:[String:Any] = ["format":["duration":String(duration),"size":String(size),"bit_rate":String(Int(Double(size)*8/duration)),"format_name":"mov,mp4 (AVFoundation adapter)"],"streams":streams]
let data = try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys])
print(String(data:data,encoding:.utf8)!)
