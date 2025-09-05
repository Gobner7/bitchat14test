import Foundation

// MARK: - Protocol TLV Packets

struct AnnouncementPacket {
    let nickname: String
    let noisePublicKey: Data            // Noise static public key (Curve25519.KeyAgreement)
    let signingPublicKey: Data          // Ed25519 public key for signing

    private enum TLVType: UInt8 {
        case nickname = 0x01
        case noisePublicKey = 0x02
        case signingPublicKey = 0x03
    }

    func encode() -> Data? {
        var data = Data()

        // TLV for nickname
        guard let nicknameData = nickname.data(using: .utf8), nicknameData.count <= 255 else { return nil }
        data.append(TLVType.nickname.rawValue)
        data.append(UInt8(nicknameData.count))
        data.append(nicknameData)

        // TLV for noise public key
        guard noisePublicKey.count <= 255 else { return nil }
        data.append(TLVType.noisePublicKey.rawValue)
        data.append(UInt8(noisePublicKey.count))
        data.append(noisePublicKey)

        // TLV for signing public key
        guard signingPublicKey.count <= 255 else { return nil }
        data.append(TLVType.signingPublicKey.rawValue)
        data.append(UInt8(signingPublicKey.count))
        data.append(signingPublicKey)

        return data
    }

    static func decode(from data: Data) -> AnnouncementPacket? {
        var offset = 0
        var nickname: String?
        var noisePublicKey: Data?
        var signingPublicKey: Data?

        while offset + 2 <= data.count {
            let typeRaw = data[offset]
            offset += 1
            let length = Int(data[offset])
            offset += 1

            guard offset + length <= data.count else { return nil }
            let value = data[offset..<offset + length]
            offset += length

            if let type = TLVType(rawValue: typeRaw) {
                switch type {
                case .nickname:
                    nickname = String(data: value, encoding: .utf8)
                case .noisePublicKey:
                    noisePublicKey = Data(value)
                case .signingPublicKey:
                    signingPublicKey = Data(value)
                }
            } else {
                // Unknown TLV; skip (tolerant decoder for forward compatibility)
                continue
            }
        }

        guard let nickname = nickname, let noisePublicKey = noisePublicKey, let signingPublicKey = signingPublicKey else { return nil }
        return AnnouncementPacket(
            nickname: nickname,
            noisePublicKey: noisePublicKey,
            signingPublicKey: signingPublicKey
        )
    }
}

struct PrivateMessagePacket {
    let messageID: String
    let content: String

    private enum TLVType: UInt8 {
        case messageID = 0x00
        case content = 0x01
    }

    func encode() -> Data? {
        var data = Data()

        // TLV for messageID
        guard let messageIDData = messageID.data(using: .utf8), messageIDData.count <= 255 else { return nil }
        data.append(TLVType.messageID.rawValue)
        data.append(UInt8(messageIDData.count))
        data.append(messageIDData)

        // TLV for content
        guard let contentData = content.data(using: .utf8), contentData.count <= 255 else { return nil }
        data.append(TLVType.content.rawValue)
        data.append(UInt8(contentData.count))
        data.append(contentData)

        return data
    }

    static func decode(from data: Data) -> PrivateMessagePacket? {
        var offset = 0
        var messageID: String?
        var content: String?

        while offset + 2 <= data.count {
            guard let type = TLVType(rawValue: data[offset]) else { return nil }
            offset += 1

            let length = Int(data[offset])
            offset += 1

            guard offset + length <= data.count else { return nil }
            let value = data[offset..<offset + length]
            offset += length

            switch type {
            case .messageID:
                messageID = String(data: value, encoding: .utf8)
            case .content:
                content = String(data: value, encoding: .utf8)
            }
        }

        guard let messageID = messageID, let content = content else { return nil }
        return PrivateMessagePacket(messageID: messageID, content: content)
    }
}

// MARK: - Private Channel Encrypted Packet (TLV envelope)

struct ChannelEncryptedPacket {
    // A stable channel identifier (first 16 bytes of HMAC-SHA256 over key material)
    let channelID: Data        // 16 bytes
    let epoch: UInt64          // key epoch (seconds / epochLen)
    let nonce24: Data          // 24 bytes XChaCha nonce
    let ciphertext: Data       // variable
    let tag: Data              // 16 bytes auth tag

    private enum TLVType: UInt8 {
        case channelID = 0x01
        case nonce24   = 0x02
        case ciphertext = 0x03
        case tag       = 0x04
        case epoch     = 0x05    // 8 bytes
    }

    func encode() -> Data? {
        guard channelID.count == 16, nonce24.count == 24, tag.count == 16 else { return nil }
        var data = Data()

        // channelID
        data.append(TLVType.channelID.rawValue)
        data.append(UInt8(channelID.count))
        data.append(channelID)

        // epoch (8 bytes)
        var epochBE = epoch.bigEndian
        let epochBytes = withUnsafeBytes(of: &epochBE) { Data($0) }
        data.append(TLVType.epoch.rawValue)
        data.append(UInt8(epochBytes.count))
        data.append(epochBytes)

        // nonce24
        data.append(TLVType.nonce24.rawValue)
        data.append(UInt8(nonce24.count))
        data.append(nonce24)

        // ciphertext (length must fit in one byte for TLV; large payloads are handled by fragmentation above this layer)
        guard ciphertext.count <= 255 else { return nil }
        data.append(TLVType.ciphertext.rawValue)
        data.append(UInt8(ciphertext.count))
        data.append(ciphertext)

        // tag
        data.append(TLVType.tag.rawValue)
        data.append(UInt8(tag.count))
        data.append(tag)

        return data
    }

    static func decode(from data: Data) -> ChannelEncryptedPacket? {
        var offset = 0
        var channelID: Data?
        var epoch: UInt64?
        var nonce24: Data?
        var ciphertext: Data?
        var tag: Data?

        while offset + 2 <= data.count {
            guard let type = TLVType(rawValue: data[offset]) else { return nil }
            offset += 1
            let length = Int(data[offset]); offset += 1
            guard offset + length <= data.count else { return nil }
            let value = data[offset..<offset+length]
            offset += length

            switch type {
            case .channelID: channelID = Data(value)
            case .epoch:
                if value.count == 8 {
                    epoch = value.withUnsafeBytes { $0.load(as: UInt64.self) }.bigEndian
                }
            case .nonce24: nonce24 = Data(value)
            case .ciphertext: ciphertext = Data(value)
            case .tag: tag = Data(value)
            }
        }

        guard let cid = channelID, let e = epoch, let n = nonce24, let c = ciphertext, let t = tag,
              cid.count == 16, n.count == 24, t.count == 16 else { return nil }
        return ChannelEncryptedPacket(channelID: cid, epoch: e, nonce24: n, ciphertext: c, tag: t)
    }
}

// MARK: - BitTransfer (channel-encrypted file transfer) TLVs

enum BitTransferType: UInt8 {
    case manifest = 0x10
    case chunk    = 0x11
    case ack      = 0x12
    case cancel   = 0x13
}

struct BitTransferManifest {
    let fileID: Data          // 16 bytes random ID
    let fileName: String
    let mimeType: String
    let fileSize: UInt64
    let totalChunks: UInt32
    let fileHash: Data        // 32 bytes SHA-256

    private enum TLVType: UInt8 {
        case fileID      = 0x01
        case fileName    = 0x02
        case mimeType    = 0x03
        case fileSize    = 0x04
        case totalChunks = 0x05
        case fileHash    = 0x06
    }

    func encode() -> Data? {
        guard fileID.count == 16, fileHash.count == 32 else { return nil }
        var data = Data([BitTransferType.manifest.rawValue])
        data.append(TLVType.fileID.rawValue);   data.append(UInt8(fileID.count));   data.append(fileID)
        guard let nameData = fileName.data(using: .utf8), nameData.count <= 255 else { return nil }
        data.append(TLVType.fileName.rawValue); data.append(UInt8(nameData.count)); data.append(nameData)
        guard let mimeData = mimeType.data(using: .utf8), mimeData.count <= 255 else { return nil }
        data.append(TLVType.mimeType.rawValue); data.append(UInt8(mimeData.count)); data.append(mimeData)
        var sizeBE = fileSize.bigEndian
        let sizeBytes = withUnsafeBytes(of: &sizeBE) { Data($0) }
        data.append(TLVType.fileSize.rawValue); data.append(UInt8(sizeBytes.count)); data.append(sizeBytes)
        var chunksBE = totalChunks.bigEndian
        let chunksBytes = withUnsafeBytes(of: &chunksBE) { Data($0) }
        data.append(TLVType.totalChunks.rawValue); data.append(UInt8(chunksBytes.count)); data.append(chunksBytes)
        data.append(TLVType.fileHash.rawValue); data.append(UInt8(fileHash.count)); data.append(fileHash)
        return data
    }

    static func decode(_ data: Data) -> BitTransferManifest? {
        guard data.first == BitTransferType.manifest.rawValue else { return nil }
        var offset = 1
        var fileID: Data?
        var fileName: String?
        var mimeType: String?
        var fileSize: UInt64?
        var totalChunks: UInt32?
        var fileHash: Data?
        while offset + 2 <= data.count {
            guard let t = TLVType(rawValue: data[offset]) else { return nil }
            offset += 1
            let len = Int(data[offset]); offset += 1
            guard offset + len <= data.count else { return nil }
            let value = data[offset..<offset+len]; offset += len
            switch t {
            case .fileID: fileID = Data(value)
            case .fileName: fileName = String(data: value, encoding: .utf8)
            case .mimeType: mimeType = String(data: value, encoding: .utf8)
            case .fileSize:
                if value.count == 8 { fileSize = value.withUnsafeBytes { $0.load(as: UInt64.self) }.bigEndian }
            case .totalChunks:
                if value.count == 4 { totalChunks = value.withUnsafeBytes { $0.load(as: UInt32.self) }.bigEndian }
            case .fileHash: fileHash = Data(value)
            }
        }
        guard let fid = fileID, let name = fileName, let mime = mimeType, let size = fileSize, let chunks = totalChunks, let hash = fileHash,
              fid.count == 16, hash.count == 32 else { return nil }
        return BitTransferManifest(fileID: fid, fileName: name, mimeType: mime, fileSize: size, totalChunks: chunks, fileHash: hash)
    }
}

struct BitTransferChunk {
    let fileID: Data         // 16 bytes
    let index: UInt32
    let totalChunks: UInt32
    let chunkHash: Data      // 32 bytes SHA-256
    let payload: Data        // <= 255 bytes (fits TLV for now)

    private enum TLVType: UInt8 {
        case fileID      = 0x01
        case index       = 0x02
        case totalChunks = 0x03
        case chunkHash   = 0x04
        case payload     = 0x05
    }

    func encode() -> Data? {
        guard fileID.count == 16, chunkHash.count == 32, payload.count <= 255 else { return nil }
        var data = Data([BitTransferType.chunk.rawValue])
        data.append(TLVType.fileID.rawValue); data.append(UInt8(fileID.count)); data.append(fileID)
        var idxBE = index.bigEndian; let idxBytes = withUnsafeBytes(of: &idxBE) { Data($0) }
        data.append(TLVType.index.rawValue); data.append(UInt8(idxBytes.count)); data.append(idxBytes)
        var totBE = totalChunks.bigEndian; let totBytes = withUnsafeBytes(of: &totBE) { Data($0) }
        data.append(TLVType.totalChunks.rawValue); data.append(UInt8(totBytes.count)); data.append(totBytes)
        data.append(TLVType.chunkHash.rawValue); data.append(UInt8(chunkHash.count)); data.append(chunkHash)
        data.append(TLVType.payload.rawValue); data.append(UInt8(payload.count)); data.append(payload)
        return data
    }

    static func decode(_ data: Data) -> BitTransferChunk? {
        guard data.first == BitTransferType.chunk.rawValue else { return nil }
        var offset = 1
        var fileID: Data?
        var index: UInt32?
        var totalChunks: UInt32?
        var chunkHash: Data?
        var payload: Data?
        while offset + 2 <= data.count {
            guard let t = TLVType(rawValue: data[offset]) else { return nil }
            offset += 1
            let len = Int(data[offset]); offset += 1
            guard offset + len <= data.count else { return nil }
            let value = data[offset..<offset+len]; offset += len
            switch t {
            case .fileID: fileID = Data(value)
            case .index: if value.count == 4 { index = value.withUnsafeBytes { $0.load(as: UInt32.self) }.bigEndian }
            case .totalChunks: if value.count == 4 { totalChunks = value.withUnsafeBytes { $0.load(as: UInt32.self) }.bigEndian }
            case .chunkHash: chunkHash = Data(value)
            case .payload: payload = Data(value)
            }
        }
        guard let fid = fileID, let i = index, let t = totalChunks, let h = chunkHash, let p = payload,
              fid.count == 16, h.count == 32 else { return nil }
        return BitTransferChunk(fileID: fid, index: i, totalChunks: t, chunkHash: h, payload: p)
    }
}

struct BitTransferAck {
    let fileID: Data       // 16 bytes
    let ackedUpTo: UInt32  // highest contiguous chunk index received

    private enum TLVType: UInt8 { case fileID = 0x01; case ackedUpTo = 0x02 }

    func encode() -> Data? {
        guard fileID.count == 16 else { return nil }
        var data = Data([BitTransferType.ack.rawValue])
        data.append(TLVType.fileID.rawValue); data.append(UInt8(fileID.count)); data.append(fileID)
        var aBE = ackedUpTo.bigEndian; let aBytes = withUnsafeBytes(of: &aBE) { Data($0) }
        data.append(TLVType.ackedUpTo.rawValue); data.append(UInt8(aBytes.count)); data.append(aBytes)
        return data
    }

    static func decode(_ data: Data) -> BitTransferAck? {
        guard data.first == BitTransferType.ack.rawValue else { return nil }
        var offset = 1
        var fileID: Data?
        var ack: UInt32?
        while offset + 2 <= data.count {
            guard let t = TLVType(rawValue: data[offset]) else { return nil }
            offset += 1
            let len = Int(data[offset]); offset += 1
            guard offset + len <= data.count else { return nil }
            let value = data[offset..<offset+len]; offset += len
            switch t {
            case .fileID: fileID = Data(value)
            case .ackedUpTo: if value.count == 4 { ack = value.withUnsafeBytes { $0.load(as: UInt32.self) }.bigEndian }
            }
        }
        guard let fid = fileID, let a = ack, fid.count == 16 else { return nil }
        return BitTransferAck(fileID: fid, ackedUpTo: a)
    }
}

struct BitTransferCancel {
    let fileID: Data // 16 bytes
    private enum TLVType: UInt8 { case fileID = 0x01 }
    func encode() -> Data? {
        guard fileID.count == 16 else { return nil }
        var data = Data([BitTransferType.cancel.rawValue])
        data.append(TLVType.fileID.rawValue); data.append(UInt8(fileID.count)); data.append(fileID)
        return data
    }
    static func decode(_ data: Data) -> BitTransferCancel? {
        guard data.first == BitTransferType.cancel.rawValue else { return nil }
        var offset = 1
        guard offset + 2 <= data.count else { return nil }
        guard let t = TLVType(rawValue: data[offset]) else { return nil }
        offset += 1
        let len = Int(data[offset]); offset += 1
        guard t == .fileID, len == 16, offset + len <= data.count else { return nil }
        let fid = Data(data[offset..<offset+len])
        return BitTransferCancel(fileID: fid)
    }
}
