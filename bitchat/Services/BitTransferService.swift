import Foundation
import CryptoKit
import Security

final class BitTransferService {
    static let shared = BitTransferService()

    struct Outgoing {
        let manifest: BitTransferManifest
        var nextIndex: UInt32
        let totalChunks: UInt32
        let chunkSize: Int
        let data: Data
        var lastAcked: UInt32
    }

    struct Incoming {
        let manifest: BitTransferManifest
        var received: Set<UInt32>
        var buffer: [UInt32: Data]
    }

    private let queue = DispatchQueue(label: "bittransfer", qos: .utility)
    private var outgoing: [Data: Outgoing] = [:] // fileID -> state
    private var incoming: [Data: Incoming] = [:]

    func buildManifest(fileName: String, mime: String, data: Data, chunkSize: Int = 192) -> BitTransferManifest? {
        let totalChunks = UInt32((data.count + chunkSize - 1) / chunkSize)
        var fileID = Data(count: 16)
        _ = fileID.withUnsafeMutableBytes { SecRandomCopyBytes(kSecRandomDefault, 16, $0.baseAddress!) }
        let hash = data.sha256()
        return BitTransferManifest(fileID: fileID, fileName: fileName, mimeType: mime, fileSize: UInt64(data.count), totalChunks: totalChunks, fileHash: hash)
    }

    func startSend(manifest: BitTransferManifest, data: Data) {
        queue.async {
            let chunkSize = 192
            let state = Outgoing(manifest: manifest, nextIndex: 0, totalChunks: manifest.totalChunks, chunkSize: chunkSize, data: data, lastAcked: UInt32.max)
            self.outgoing[manifest.fileID] = state
        }
    }

    func nextChunks(for fileID: Data, window: Int = 4) -> [BitTransferChunk] {
        return queue.sync {
            guard var st = outgoing[fileID] else { return [] }
            var chunks: [BitTransferChunk] = []
            var count = 0
            while count < window && st.nextIndex < st.totalChunks {
                let idx = st.nextIndex
                let start = Int(idx) * st.chunkSize
                let end = min(start + st.chunkSize, st.data.count)
                let slice = st.data.subdata(in: start..<end)
                let h = slice.sha256()
                if let encoded = BitTransferChunk(fileID: fileID, index: idx, totalChunks: st.totalChunks, chunkHash: h, payload: slice).encode(),
                   let decoded = BitTransferChunk.decode(encoded) {
                    chunks.append(decoded)
                }
                st.nextIndex += 1
                count += 1
            }
            outgoing[fileID] = st
            return chunks
        }
    }

    func handleAck(_ ack: BitTransferAck) {
        queue.async {
            guard var st = self.outgoing[ack.fileID] else { return }
            st.lastAcked = max(st.lastAcked, ack.ackedUpTo)
            self.outgoing[ack.fileID] = st
        }
    }

    func handleManifest(_ m: BitTransferManifest) {
        queue.async {
            if self.incoming[m.fileID] == nil {
                self.incoming[m.fileID] = Incoming(manifest: m, received: [], buffer: [:])
            }
        }
    }

    func handleChunk(_ c: BitTransferChunk) -> BitTransferAck? {
        return queue.sync {
            guard var st = incoming[c.fileID] else { return nil }
            // verify hash
            if c.chunkHash != c.payload.sha256() { return nil }
            st.buffer[c.index] = c.payload
            st.received.insert(c.index)
            incoming[c.fileID] = st
            // compute highest contiguous
            var idx: UInt32 = 0
            while st.received.contains(idx) { idx += 1 }
            return BitTransferAck(fileID: c.fileID, ackedUpTo: idx > 0 ? idx - 1 : 0)
        }
    }

    func assembleIfComplete(_ fileID: Data) -> Data? {
        return queue.sync {
            guard let st = incoming[fileID] else { return nil }
            if st.received.count != Int(st.manifest.totalChunks) { return nil }
            var out = Data(capacity: Int(st.manifest.fileSize))
            for i in 0..<st.manifest.totalChunks { if let p = st.buffer[i] { out.append(p) } }
            return out.sha256() == st.manifest.fileHash ? out : nil
        }
    }

    func manifest(for fileID: Data) -> BitTransferManifest? {
        return queue.sync { incoming[fileID]?.manifest }
    }
}

private extension Data {
    func sha256() -> Data { Data(SHA256.hash(data: self)) }
}

