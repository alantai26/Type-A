import SwiftUI

struct SignupView: View {
    @Environment(AuthStore.self) private var authStore
    @Environment(\.dismiss) private var dismiss

    @State private var displayName = ""
    @State private var email = ""
    @State private var password = ""
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        VStack(spacing: 0) {
            VStack(spacing: 8) {
                Text("Create Account")
                    .font(.system(size: 32, weight: .bold, design: .rounded))
                Text("Start planning outings you'll love.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
            }
            .padding(.top, 32)
            .padding(.bottom, 32)

            VStack(spacing: 12) {
                TextField("Display Name", text: $displayName)
                    .textContentType(.name)
                    .textInputAutocapitalization(.words)
                    .autocorrectionDisabled()
                    .padding(14)
                    .background(Color(.secondarySystemBackground))
                    .clipShape(RoundedRectangle(cornerRadius: 12))

                TextField("Email", text: $email)
                    .textContentType(.emailAddress)
                    .keyboardType(.emailAddress)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .padding(14)
                    .background(Color(.secondarySystemBackground))
                    .clipShape(RoundedRectangle(cornerRadius: 12))

                SecureField("Password", text: $password)
                    .textContentType(.newPassword)
                    .padding(14)
                    .background(Color(.secondarySystemBackground))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            }

            if let errorMessage {
                Text(errorMessage)
                    .font(.callout)
                    .foregroundStyle(.red)
                    .multilineTextAlignment(.center)
                    .padding(.top, 12)
            }

            Button {
                Task { await signUp() }
            } label: {
                if isLoading {
                    ProgressView()
                        .frame(maxWidth: .infinity)
                        .tint(.white)
                } else {
                    Text("Sign Up")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                }
            }
            .padding(.vertical, 14)
            .background(Color.accentColor)
            .foregroundStyle(.white)
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .disabled(isLoading || email.isEmpty || password.isEmpty || displayName.isEmpty)
            .opacity((email.isEmpty || password.isEmpty || displayName.isEmpty) ? 0.5 : 1)
            .padding(.top, 16)

            Spacer()

            Button("Cancel") {
                dismiss()
            }
            .foregroundStyle(.secondary)
            .padding(.bottom, 24)
        }
        .padding(.horizontal, 24)
    }

    func signUp() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            try await authStore.signUp(email: email, password: password, displayName: displayName)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
