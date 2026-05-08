import SwiftUI                                                       
                                                                       
struct MainTabView: View {                                           
    var body: some View {
        TabView {
            FeedView()
                .tabItem { Label("Feed", systemImage: "newspaper")
                }                                                                   
            PlanView()                                               
                .tabItem { Label("Plan", systemImage: "calendar")                                    
                }                                                            
            SearchView()                                               
                .tabItem { Label("Search", systemImage: "magnifyingglass")
                }
            ProfileView()                                               
                .tabItem { Label("Profile", systemImage: "person.circle")
                }
        }
    }  
}