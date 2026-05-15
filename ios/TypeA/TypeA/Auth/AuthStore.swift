import Foundation
import Supabase

@MainActor
@Observable
final class AuthStore {
    var isAuthenticated: Bool = false
    var currentUser: User?
    var isInitializing: Bool = true

    private var stateChangeTask: Task<Void, Never>?

    init() {
        let initial = AuthService.shared.client.auth.currentSession
        isAuthenticated = (initial != nil && initial?.isExpired == false)
        isInitializing = false

        if isAuthenticated {
            Task { await loadCurrentUser() }
        }

        stateChangeTask = Task { [weak self] in
            for await (_, session) in AuthService.shared.client.auth.authStateChanges {
                guard let self else { return }
                let nowAuthenticated = (session != nil)
                self.isAuthenticated = nowAuthenticated
                if nowAuthenticated {
                    await self.loadCurrentUser()
                } else {
                    self.currentUser = nil
                }
            }
        }
    }

    func signIn(email: String, password: String) async throws {
        try await AuthService.shared.signIn(email: email, password: password)
    }

    func signUp(email: String, password: String, displayName: String) async throws {
        try await AuthService.shared.signUp(email: email, password: password)
        let body = UserUpdate(displayName: displayName, bio: nil)
        let updated: User = try await APIClient.shared.request("/me", method: "PATCH", body: body)
        currentUser = updated
    }

    func signOut() async throws {
        try await AuthService.shared.signOut()
    }

    private func loadCurrentUser() async {
        do {
            let user: User = try await APIClient.shared.request("/me")
            currentUser = user
        } catch {
            print("AuthStore: failed to load /me — \(error)")
        }
    }
}
