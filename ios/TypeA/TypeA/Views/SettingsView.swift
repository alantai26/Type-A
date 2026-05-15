import SwiftUI

private enum EditableField: String, Identifiable {
    case displayName, bio
    var id: String { rawValue }
    var title: String {
        switch self {
        case .displayName: return "Display Name"
        case .bio: return "Bio"
        }
    }
}

struct SettingsView: View {
    @Environment(AuthStore.self) private var authStore
    @Environment(\.dismiss) private var dismiss

    @State private var displayName: String = ""
    @State private var bio: String = ""
    @State private var isSaving = false
    @State private var isSigningOut = false
    @State private var errorMessage: String?
    @State private var editingField: EditableField?

    private static let bioMaxLength = 160

    var body: some View {
        Form {
            Section("Edit Profile") {
                editableRow(
                    label: "Display Name",
                    value: displayName,
                    placeholder: "Not set",
                    onTap: { editingField = .displayName }
                )

                editableRow(
                    label: "Bio",
                    value: bio,
                    placeholder: "Add a bio",
                    onTap: { editingField = .bio }
                )

                if let errorMessage {
                    Text(errorMessage)
                        .font(.footnote)
                        .foregroundStyle(.red)
                }
            }

            Section("Notifications") {
                Text("Coming soon")
                    .foregroundStyle(.secondary)
            }
            .disabled(true)

            Section("Privacy") {
                Text("Coming soon")
                    .foregroundStyle(.secondary)
            }
            .disabled(true)

            Section("Blocked users") {
                Text("Coming soon")
                    .foregroundStyle(.secondary)
            }
            .disabled(true)

            Section {
                Button(role: .destructive) {
                    Task { await signOut() }
                } label: {
                    if isSigningOut {
                        ProgressView()
                            .frame(maxWidth: .infinity)
                    } else {
                        Text("Logout")
                            .frame(maxWidth: .infinity)
                    }
                }
                .disabled(isSigningOut)
            }
        }
        .navigationTitle("Settings")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("Save") {
                    Task { await save() }
                }
                .disabled(!hasChanges || isSaving)
            }
        }
        .onAppear {
            displayName = authStore.currentUser?.displayName ?? ""
            bio = authStore.currentUser?.bio ?? ""
        }
        .sheet(item: $editingField) { field in
            EditFieldSheet(
                field: field,
                displayName: $displayName,
                bio: $bio,
                bioMaxLength: Self.bioMaxLength
            )
        }
    }

    private func editableRow(
        label: String,
        value: String,
        placeholder: String,
        onTap: @escaping () -> Void
    ) -> some View {
        Button(action: onTap) {
            HStack(spacing: 12) {
                Text(label)
                    .font(.body.weight(.semibold))
                    .foregroundStyle(.primary)

                Spacer(minLength: 12)

                Text(value.isEmpty ? placeholder : value)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
                    .truncationMode(.tail)

                Image(systemName: "pencil")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundStyle(.secondary)
            }
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }

    private var hasChanges: Bool {
        let currentName = authStore.currentUser?.displayName ?? ""
        let currentBio = authStore.currentUser?.bio ?? ""
        return displayName != currentName || bio != currentBio
    }

    private func save() async {
        let trimmedName = displayName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedName.isEmpty else {
            errorMessage = "Display name can't be empty"
            return
        }

        isSaving = true
        defer { isSaving = false }
        errorMessage = nil

        let body = UserUpdate(
            displayName: trimmedName,
            bio: bio.trimmingCharacters(in: .whitespacesAndNewlines)
        )

        do {
            let updated: User = try await APIClient.shared.request(
                "/me", method: "PATCH", body: body
            )
            authStore.currentUser = updated
            dismiss()
        } catch {
            errorMessage = "Couldn't save — try again"
            print("SettingsView: PATCH /me failed — \(error)")
        }
    }

    private func signOut() async {
        isSigningOut = true
        defer { isSigningOut = false }
        try? await authStore.signOut()
    }
}

private struct EditFieldSheet: View {
    let field: EditableField
    @Binding var displayName: String
    @Binding var bio: String
    let bioMaxLength: Int

    @Environment(\.dismiss) private var dismiss
    @State private var draft: String = ""
    @FocusState private var isFocused: Bool

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    if field == .bio {
                        TextField("Add a bio", text: $draft, axis: .vertical)
                            .lineLimit(3...6)
                            .focused($isFocused)
                            .onChange(of: draft) { _, newValue in
                                if newValue.count > bioMaxLength {
                                    draft = String(newValue.prefix(bioMaxLength))
                                }
                            }
                    } else {
                        TextField("Display name", text: $draft)
                            .textInputAutocapitalization(.words)
                            .focused($isFocused)
                    }
                }

                if field == .bio {
                    Section {
                        HStack {
                            Spacer()
                            Text("\(draft.count) / \(bioMaxLength)")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .monospacedDigit()
                        }
                    }
                }
            }
            .navigationTitle(field.title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") {
                        switch field {
                        case .displayName: displayName = draft
                        case .bio: bio = draft
                        }
                        dismiss()
                    }
                    .fontWeight(.semibold)
                }
            }
            .onAppear {
                draft = (field == .displayName) ? displayName : bio
                isFocused = true
            }
        }
    }
}
