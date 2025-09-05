//
// PrivateChannelManager.swift
// bitchat
//
// Tracks joined private channels and provides active selection.
// Stores derived keys securely via KeychainManager.
//

import Foundation
import Combine

final class PrivateChannelManager: ObservableObject {
    static let shared = PrivateChannelManager()

    @Published private(set) var joined: [String: ChannelCrypto.Derived] = [:] // normalizedName -> Derived
    @Published var activeChannel: String? = nil // normalized name (without '#')

    private let storageKey = "bitchat.privateChannels.v2"

    private init() {
        load()
    }

    func join(channelName: String, password: String) {
        let derived = ChannelCrypto.deriveKey(channelName: channelName, password: password)
        let norm = ChannelCrypto.normalizeChannelName(channelName)
        joined[norm] = derived
        if activeChannel == nil { activeChannel = norm }
        save()
    }

    func leave(channelName: String) {
        let norm = ChannelCrypto.normalizeChannelName(channelName)
        joined.removeValue(forKey: norm)
        if activeChannel == norm { activeChannel = joined.keys.first }
        save()
    }

    func select(channelName: String) {
        let norm = ChannelCrypto.normalizeChannelName(channelName)
        guard joined[norm] != nil else { return }
        activeChannel = norm
    }

    func list() -> [String] {
        return Array(joined.keys).sorted()
    }

    func keyForActive() -> ChannelCrypto.Derived? {
        guard let name = activeChannel else { return nil }
        return joined[name]
    }

    // MARK: - Persistence
    private func save() {
        // Persist small map: name -> (key, cid)
        var dict: [String: String] = [:]
        for (name, d) in joined {
            var epochBE = d.epochLenSec.bigEndian
            let epochBytes = withUnsafeBytes(of: &epochBE) { Data($0) }
            dict[name] = (d.key32 + d.channelID16 + epochBytes).hexEncodedString()
        }
        if let data = try? JSONSerialization.data(withJSONObject: dict, options: []) {
            _ = KeychainManager.shared.saveIdentityKey(data, forKey: storageKey)
        }
    }

    private func load() {
        guard let data = KeychainManager.shared.getIdentityKey(forKey: storageKey) else { return }
        guard let obj = try? JSONSerialization.jsonObject(with: data, options: []),
              let dict = obj as? [String: String] else { return }
        var out: [String: ChannelCrypto.Derived] = [:]
        for (name, hex) in dict {
            if let raw = Data(hexString: hex), raw.count >= (32 + 16 + 8) {
                let key = raw.prefix(32)
                let cid = raw.dropFirst(32).prefix(16)
                let epochData = raw.suffix(8)
                let epoch = epochData.withUnsafeBytes { $0.load(as: UInt64.self) }.bigEndian
                out[name] = ChannelCrypto.Derived(key32: key, channelID16: cid, epochLenSec: epoch)
            }
        }
        joined = out
        if activeChannel == nil { activeChannel = joined.keys.first }
    }
}

