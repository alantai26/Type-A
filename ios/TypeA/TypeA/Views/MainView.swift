import SwiftUI

struct MainView: View {
    @Environment(AuthStore.self) private var authStore
    @State private var isSigningOut = false

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            if let user = authStore.currentUser {
                VStack(spacing: 6) {
                    Text("Hi, \(user.displayName)")
                        .font(.system(size: 32, weight: .bold, design: .rounded))
                    Text(user.email)
                        .font(.callout)
                        .foregroundStyle(.secondary)
                }
            } else {
                ProgressView()
            }

            Spacer()

            Button {
                Task { await signOut() }
            } label: {
                if isSigningOut {
                    ProgressView()
                        .frame(maxWidth: .infinity)
                } else {
                    Text("Logout")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                }
            }
            .padding(.vertical, 14)
            .foregroundStyle(.red)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(Color.red.opacity(0.3), lineWidth: 1)
            )
            .disabled(isSigningOut)
            .padding(.bottom, 24)
        }
        .padding(.horizontal, 24)
    }

    func signOut() async {
        isSigningOut = true
        defer { isSigningOut = false }
        try? await authStore.signOut()
    }
}
