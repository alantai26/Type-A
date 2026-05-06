import Foundation

enum AppConfig {
    static let supabaseURL: URL = {
        guard let s = Bundle.main.object(forInfoDictionaryKey: "SupabaseURL") as? String,
              let url = URL(string: s) else {
            fatalError("Missing or invalid SupabaseURL in Info.plist — check Local.xcconfig")
        }
        return url
    }()

    static let supabasePublishableKey: String = {
        guard let s = Bundle.main.object(forInfoDictionaryKey: "SupabasePublishableKey") as? String,
              !s.isEmpty else {
            fatalError("Missing SupabasePublishableKey in Info.plist — check Local.xcconfig")
        }
        return s
    }()

    static let apiBaseURL: URL = {
        guard let s = Bundle.main.object(forInfoDictionaryKey: "APIBaseURL") as? String,
              let url = URL(string: s) else {
            fatalError("Missing or invalid APIBaseURL in Info.plist — check Local.xcconfig")
        }
        return url
    }()
}
