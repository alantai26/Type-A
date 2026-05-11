import SwiftUI

private enum ProfileTab: String, CaseIterable, Identifiable {
    case places, outings, saved
    var id: String { rawValue }
    var title: String {
        switch self {
        case .places: return "Places"
        case .outings: return "Outings"
        case .saved: return "Saved"
        }
    }
}

private struct EmptyStateSpec {
    let icon: String
    let title: String
    let subtext: String
    let ctaLabel: String
    let targetTab: AppTab
}

struct ProfileView: View {
    @Environment(AuthStore.self) private var authStore
    @Environment(TabSelectionStore.self) private var tabSelection
    @State private var selectedTab: ProfileTab = .places
    @State private var isSigningOut = false

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                headerRow
                identityBlock
                    .padding(.top, 8)
                friendsRow
                    .padding(.top, 20)
                tabStrip
                    .padding(.top, 28)
                emptyStateCard
                    .padding(.top, 40)
                Spacer(minLength: 24)
                logoutButton
                    .padding(.top, 48)
                    .padding(.bottom, 24)
            }
            .padding(.horizontal, 24)
        }
    }

    private var headerRow: some View {
        HStack {
            Spacer()
            Button {
                // settings sheet — follow-up ticket
            } label: {
                Image(systemName: "gearshape")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundStyle(.primary)
                    .padding(10)
                    .background(Color(uiColor: .secondarySystemBackground))
                    .clipShape(Circle())
            }
        }
        .padding(.top, 8)
    }

    private var identityBlock: some View {
        HStack(spacing: 16) {
            initialsAvatar(name: authStore.currentUser?.displayName ?? "?", size: 60)

            VStack(alignment: .leading, spacing: 4) {
                Text(authStore.currentUser?.displayName ?? " ")
                    .font(.system(size: 24, weight: .bold, design: .rounded))
                Text("Tap settings to add a bio")
                    .font(.callout)
                    .italic()
                    .foregroundStyle(.secondary)
            }

            Spacer()
        }
    }

    private func initialsAvatar(name: String, size: CGFloat) -> some View {
        let initial = name.first.map { String($0).uppercased() } ?? "?"
        return Text(initial)
            .font(.system(size: size * 0.42, weight: .bold, design: .rounded))
            .foregroundStyle(.white)
            .frame(width: size, height: size)
            .background(Color.accentColor)
            .clipShape(Circle())
    }

    private var friendsRow: some View {
        Button {
            // Friends sub-screen — follow-up ticket
        } label: {
            HStack(spacing: 12) {
                Image(systemName: "person")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(.secondary)
                    .frame(width: 28, height: 28)
                    .background(Color(uiColor: .tertiarySystemBackground))
                    .clipShape(Circle())

                Text("0 friends")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundStyle(.primary)

                Spacer()

                Image(systemName: "chevron.right")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(.secondary)
            }
            .padding(14)
            .background(Color(uiColor: .secondarySystemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(.plain)
    }

    private var tabStrip: some View {
        HStack(spacing: 0) {
            ForEach(ProfileTab.allCases) { tab in
                tabStripItem(tab: tab)
            }
        }
        .overlay(alignment: .bottom) {
            Rectangle()
                .fill(Color(uiColor: .separator))
                .frame(height: 0.5)
        }
    }

    private func tabStripItem(tab: ProfileTab) -> some View {
        let isActive = tab == selectedTab
        return Button {
            withAnimation(.easeInOut(duration: 0.15)) {
                selectedTab = tab
            }
        } label: {
            VStack(spacing: 10) {
                HStack(spacing: 6) {
                    Text(tab.title)
                        .font(.system(size: 15, weight: .semibold))
                    Text("0")
                        .font(.system(size: 14, weight: .semibold))
                }
                .foregroundStyle(isActive ? Color.accentColor : Color.secondary)

                Rectangle()
                    .fill(isActive ? Color.accentColor : Color.clear)
                    .frame(height: 2)
            }
            .frame(maxWidth: .infinity)
        }
        .buttonStyle(.plain)
    }

    private var emptyStateCard: some View {
        let spec = emptyStateSpec(for: selectedTab)
        return VStack(spacing: 14) {
            ZStack {
                Circle()
                    .fill(Color.accentColor.opacity(0.15))
                    .frame(width: 56, height: 56)
                Image(systemName: spec.icon)
                    .font(.system(size: 22, weight: .medium))
                    .foregroundStyle(Color.accentColor)
            }

            Text(spec.title)
                .font(.system(size: 16, weight: .semibold, design: .rounded))

            Text(spec.subtext)
                .font(.system(size: 14))
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 24)

            Button {
                tabSelection.current = spec.targetTab
            } label: {
                Text(spec.ctaLabel)
                    .font(.system(size: 14, weight: .semibold))
                    .padding(.horizontal, 18)
                    .padding(.vertical, 10)
                    .background(Color.accentColor)
                    .foregroundStyle(.white)
                    .clipShape(Capsule())
            }
            .padding(.top, 4)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 32)
    }

    private func emptyStateSpec(for tab: ProfileTab) -> EmptyStateSpec {
        switch tab {
        case .places:
            return EmptyStateSpec(
                icon: "star",
                title: "No places yet",
                subtext: "Click Search and rate your first place!",
                ctaLabel: "Find places to rate",
                targetTab: .search
            )
        case .outings:
            return EmptyStateSpec(
                icon: "calendar",
                title: "No outings yet",
                subtext: "Plan your first outing and rate it!",
                ctaLabel: "Plan an outing",
                targetTab: .plan
            )
        case .saved:
            return EmptyStateSpec(
                icon: "bookmark",
                title: "Nothing saved yet",
                subtext: "Search and save a place you want to go!",
                ctaLabel: "Find places",
                targetTab: .search
            )
        }
    }

    private var logoutButton: some View {
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
    }

    func signOut() async {
        isSigningOut = true
        defer { isSigningOut = false }
        try? await authStore.signOut()
    }
}
