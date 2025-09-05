//
// ChannelCrypto.swift
// bitchat
//
// Provides HKDF-based key derivation and XChaCha20-Poly1305 sealing/opening
// for private channel messages derived from channel name + password.
//

import Foundation
import CryptoKit
import Security

struct ChannelCrypto {
    struct Derived {
        let key32: Data       // 32-byte symmetric key
        let channelID16: Data // 16-byte channel identifier (HMAC prefix)
    }

    static func normalizeChannelName(_ raw: String) -> String {
        var s = raw.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        if s.hasPrefix("#") { s.removeFirst() }
        return s
    }

    // Derive a stable per-channel key and identifier
    static func deriveKey(channelName: String, password: String) -> Derived {
        let name = normalizeChannelName(channelName)
        // Domain-separated preimage
        let preimage = Data("bitchat:chan:v1|".utf8) + Data(name.utf8) + Data("|".utf8) + Data(password.utf8)
        // HKDF-SHA256 with empty salt, info label
        let key = HKDF<SHA256>.deriveKey(
            inputKeyMaterial: SymmetricKey(data: preimage.sha256()),
            salt: Data(),
            info: Data("bitchat-channel-v1".utf8),
            outputByteCount: 32
        )
        let keyData = key.withUnsafeBytes { Data($0) }
        // ChannelID = first 16 bytes of HMAC(key, "id")
        let mac = HMAC<SHA256>.authenticationCode(for: Data("id".utf8), using: SymmetricKey(data: keyData))
        let channelID = Data(mac).prefix(16)
        return Derived(key32: keyData, channelID16: channelID)
    }

    // Seal plaintext into ChannelEncryptedPacket
    static func seal(message: Data, channelKey: Derived, aad: Data?) throws -> ChannelEncryptedPacket {
        // 24-byte random nonce
        var nonce = Data(count: 24)
        _ = nonce.withUnsafeMutableBytes { ptr in
            SecRandomCopyBytes(kSecRandomDefault, 24, ptr.baseAddress!)
        }
        let aadFull = (aad ?? Data()) + channelKey.channelID16
        let sealed = try XChaCha20Poly1305Compat.seal(plaintext: message, key: channelKey.key32, nonce24: nonce, aad: aadFull)
        return ChannelEncryptedPacket(channelID: channelKey.channelID16, nonce24: nonce, ciphertext: sealed.ciphertext, tag: sealed.tag)
    }

    // Open ChannelEncryptedPacket; returns plaintext if channel matches
    static func open(packet: ChannelEncryptedPacket, candidate: Derived, aad: Data?) throws -> Data? {
        // Ensure channel id matches
        guard packet.channelID == candidate.channelID16 else { return nil }
        let aadFull = (aad ?? Data()) + candidate.channelID16
        return try XChaCha20Poly1305Compat.open(ciphertext: packet.ciphertext, tag: packet.tag, key: candidate.key32, nonce24: packet.nonce24, aad: aadFull)
    }
}

private extension Data {
    func sha256() -> Data {
        let d = SHA256.hash(data: self)
        return Data(d)
    }
}

