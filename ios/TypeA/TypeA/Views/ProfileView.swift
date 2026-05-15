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
    @State private var placeRatings: [PlaceRating]?
    @State private var outings: [Outing]?
    @State private var savedPlaces: [Place]?

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
                tabContent
                    .padding(.top, 20)
            }
            .padding(.horizontal, 24)
        }
        .task {
            async let p: () = loadPlaceRatings()
            async let o: () = loadOutings()
            async let s: () = loadSavedPlaces()
            _ = await (p, o, s)
        }
        .refreshable {
            async let p: () = loadPlaceRatings()
            async let o: () = loadOutings()
            async let s: () = loadSavedPlaces()
            _ = await (p, o, s)
        }
    }

    private var headerRow: some View {
        HStack {
            Spacer()
            NavigationLink {
                SettingsView()
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
                Text(authStore.currentUser?.bio ?? "Tap settings to add bio")
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
                    Text("\(countFor(tab: tab))")
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

    @ViewBuilder
    private var tabContent: some View {
        switch selectedTab {
        case .places:
            if let ratings = placeRatings {
                if ratings.isEmpty {
                    emptyStateCard
                } else {
                    placesList(ratings)
                }
            } else {
                ProgressView()
                    .padding(.vertical, 60)
            }
        case .outings:
            if let outings {
                if outings.isEmpty {
                    emptyStateCard
                } else {
                    outingsList(outings)
                }
            } else {
                ProgressView()
                    .padding(.vertical, 60)
            }
        case .saved:
            if let savedPlaces {
                if savedPlaces.isEmpty {
                    emptyStateCard
                } else {
                    savedPlacesList(savedPlaces)
                }
            } else {
                ProgressView()
                    .padding(.vertical, 60)
            }
        }
    }

    private func savedPlacesList(_ places: [Place]) -> some View {
        VStack(spacing: 0) {
            ForEach(Array(places.enumerated()), id: \.element.placeId) { idx, place in
                savedPlaceRow(place: place)
                if idx < places.count - 1 {
                    Divider()
                }
            }
        }
    }

    private func savedPlaceRow(place: Place) -> some View {
        HStack(spacing: 12) {
            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color.accentColor.opacity(0.15))
                Image(systemName: iconName(for: place.category))
                    .font(.system(size: 14, weight: .medium))
                    .foregroundStyle(Color.accentColor)
            }
            .frame(width: 32, height: 32)

            VStack(alignment: .leading, spacing: 2) {
                Text(place.name)
                    .font(.system(size: 15, weight: .semibold))
                Text(place.category)
                    .font(.system(size: 13))
                    .foregroundStyle(.secondary)
            }

            Spacer()

            Image(systemName: "bookmark.fill")
                .font(.system(size: 16, weight: .medium))
                .foregroundStyle(Color.accentColor)
        }
        .padding(.vertical, 14)
    }

    private func placesList(_ ratings: [PlaceRating]) -> some View {
        VStack(spacing: 0) {
            ForEach(Array(ratings.enumerated()), id: \.element.ratingId) { idx, rating in
                placeRatingRow(rank: idx + 1, rating: rating)
                if idx < ratings.count - 1 {
                    Divider()
                }
            }
        }
    }

    private func outingsList(_ outings: [Outing]) -> some View {
        VStack(spacing: 0) {
            ForEach(Array(outings.enumerated()), id: \.element.outingId) { idx, outing in
                outingRow(rank: idx + 1, outing: outing)
                if idx < outings.count - 1 {
                    Divider()
                }
            }
        }
    }

    private func outingRow(rank: Int, outing: Outing) -> some View {
        HStack(spacing: 12) {
            Text("\(rank)")
                .font(.system(size: 15, weight: .semibold, design: .rounded))
                .foregroundStyle(.secondary)
                .frame(width: 20, alignment: .leading)

            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color.accentColor.opacity(0.15))
                Image(systemName: "calendar")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundStyle(Color.accentColor)
            }
            .frame(width: 32, height: 32)

            VStack(alignment: .leading, spacing: 2) {
                Text(outing.title)
                    .font(.system(size: 15, weight: .semibold))
                Text(outingMeta(outing))
                    .font(.system(size: 13))
                    .foregroundStyle(.secondary)
            }

            Spacer()

            scorePill(outing.finalRating ?? 0)
        }
        .padding(.vertical, 14)
    }

    private func outingMeta(_ outing: Outing) -> String {
        let stops = "\(outing.events.count) stops"
        guard let date = outing.completedAt else { return stops }
        let dateStr = date.formatted(.dateTime.weekday(.abbreviated).month(.abbreviated).day())
        return "\(stops) · \(dateStr)"
    }

    private func placeRatingRow(rank: Int, rating: PlaceRating) -> some View {
        HStack(spacing: 12) {
            Text("\(rank)")
                .font(.system(size: 15, weight: .semibold, design: .rounded))
                .foregroundStyle(.secondary)
                .frame(width: 20, alignment: .leading)

            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color.accentColor.opacity(0.15))
                Image(systemName: iconName(for: rating.category))
                    .font(.system(size: 14, weight: .medium))
                    .foregroundStyle(Color.accentColor)
            }
            .frame(width: 32, height: 32)

            VStack(alignment: .leading, spacing: 2) {
                Text(rating.placeName)
                    .font(.system(size: 15, weight: .semibold))
                Text(rating.category)
                    .font(.system(size: 13))
                    .foregroundStyle(.secondary)
            }

            Spacer()

            scorePill(rating.rating)
        }
        .padding(.vertical, 14)
    }

    private func scorePill(_ rating: Double) -> some View {
        let colors = scoreColors(for: rating)
        return Text(String(format: "%.1f", rating))
            .font(.system(size: 15, weight: .bold, design: .rounded))
            .foregroundStyle(colors.text)
            .padding(.horizontal, 10)
            .padding(.vertical, 4)
            .background(colors.bg)
            .clipShape(Capsule())
    }

    private func scoreColors(for rating: Double) -> (bg: Color, text: Color) {
        if rating >= 6.7 {
            return (
                Color(red: 0.91, green: 0.97, blue: 0.93),
                Color(red: 0.12, green: 0.54, blue: 0.25)
            )
        } else if rating >= 3.4 {
            return (
                Color(red: 1.00, green: 0.96, blue: 0.90),
                Color(red: 0.55, green: 0.41, blue: 0.08)
            )
        } else {
            return (
                Color(red: 0.99, green: 0.93, blue: 0.93),
                Color(red: 0.78, green: 0.16, blue: 0.16)
            )
        }
    }

    private func countFor(tab: ProfileTab) -> Int {
        switch tab {
        case .places: return placeRatings?.count ?? 0
        case .outings: return outings?.count ?? 0 
        case .saved: return savedPlaces?.count ?? 0
        }
    }

    private func iconName(for category: String) -> String {
        switch category.lowercased() {
        case "activity": return "flag.fill"
        case "restaurant": return "fork.knife"
        case "bar", "cocktail bar": return "wineglass"
        case "brewery", "beer": return "mug.fill"
        case "cafe", "coffee": return "cup.and.saucer.fill"
        case "park": return "tree.fill"
        default: return "mappin"
        }
    }

    private func loadPlaceRatings() async {
        do {
            let ratings: [PlaceRating] = try await APIClient.shared.request("/me/place_ratings")
            placeRatings = ratings
        } catch {
            print("ProfileView: failed to load /me/place_ratings — \(error)")
            placeRatings = []
        }
    }

    private func loadOutings() async {
        do {
            let allOutings: [Outing] = try await APIClient.shared.request("/me/outings")
                
            outings = allOutings
                .filter { $0.status == "completed" && $0.finalRating != nil }
                .sorted { ($0.finalRating ?? 0) > ($1.finalRating ?? 0) }
        } catch {
            print("ProfileView: failed to load /me/outings — \(error)")
            outings = []
        }
    }

    private func loadSavedPlaces() async {
        do {
            let places: [Place] = try await APIClient.shared.request("/saved_places")
            savedPlaces = places
        } catch {
            print("ProfileView: failed to load /saved_places — \(error)")
            savedPlaces = []
        }
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
}
