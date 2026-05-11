import SwiftUI

struct MainTabView: View {
    @Environment(TabSelectionStore.self) private var tabSelection

    var body: some View {
        @Bindable var tabSelection = tabSelection
        TabView(selection: $tabSelection.current) {
            FeedView()
                .tabItem { Label("Feed", systemImage: "newspaper") }
                .tag(AppTab.feed)
            PlanView()
                .tabItem { Label("Plan", systemImage: "calendar") }
                .tag(AppTab.plan)
            SearchView()
                .tabItem { Label("Search", systemImage: "magnifyingglass") }
                .tag(AppTab.search)
            ProfileView()
                .tabItem { Label("Profile", systemImage: "person.circle") }
                .tag(AppTab.profile)
        }
    }
}
