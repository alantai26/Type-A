import Foundation
import Supabase

struct AuthError: Error, LocalizedError {
    let message: String
    var errorDescription: String? { message }
}

final class AuthService {
    static let shared = AuthService()

    let client: SupabaseClient

    private init() {
        client = SupabaseClient(
            supabaseURL: AppConfig.supabaseURL,
            supabaseKey: AppConfig.supabasePublishableKey,
            options: SupabaseClientOptions(
                auth: SupabaseClientOptions.AuthOptions(
                    emitLocalSessionAsInitialSession: true
                )
            )
        )
    }

    func signIn(email: String, password: String) async throws {
        try await client.auth.signIn(email: email, password: password)
    }

    func signUp(email: String, password: String) async throws {
        let response = try await client.auth.signUp(email: email, password: password)
        if response.session == nil {
            throw AuthError(message: "Account created — check your email to confirm, then sign in.")
        }
    }

    func signOut() async throws {
        try await client.auth.signOut()
    }

    func currentAccessToken() async -> String? {
        try? await client.auth.session.accessToken
    }
}
