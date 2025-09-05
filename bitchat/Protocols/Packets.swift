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
