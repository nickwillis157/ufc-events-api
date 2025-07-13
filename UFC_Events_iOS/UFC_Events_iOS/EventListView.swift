import SwiftUI

struct EventListView: View {
    @StateObject private var networkService = NetworkService.shared
    @State private var events: [UFCEvent] = []
    @State private var filteredEvents: [UFCEvent] = []
    @State private var currentView: EventViewType = .upcoming
    @State private var searchTerm: String = ""
    @State private var yearFilter: String = ""
    @State private var statusFilter: String = ""
    @State private var availableYears: [String] = []
    @State private var isLoading: Bool = true
    @State private var errorMessage: String?
    
    // Pagination state
    @State private var currentPage: Int = 1
    @State private var hasMorePages: Bool = true
    @State private var isLoadingMore: Bool = false

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                headerView
                
                ScrollView {
                    VStack(spacing: 20) {
                        controlsView
                        
                        if isLoading {
                            loadingView
                        } else if let errorMessage = errorMessage {
                            errorView(message: errorMessage)
                        } else if filteredEvents.isEmpty {
                            noResultsView
                        } else {
                            eventsGridView
                        }
                    }
                    .padding(.horizontal)
                    .padding(.top, 20)
                }
            }
            .background(Color.black.edgesIgnoringSafeArea(.all))
            .navigationBarHidden(true)
            .onAppear(perform: loadEvents)
        }
    }
    
    // MARK: - Subviews
    
    private var headerView: some View {
        VStack {
            HStack {
                titleText
                Spacer()
                navigationButtons
            }
            .padding(.horizontal)
            .padding(.vertical, 10)
            .background(headerBackground)
            .overlay(headerBorder, alignment: .bottom)
        }
    }
    
    private var titleText: some View {
        Text("UFC Events")
            .font(.largeTitle)
            .fontWeight(.heavy)
            .foregroundColor(.white)
    }
    
    private var navigationButtons: some View {
        HStack(spacing: 8) {
            ForEach(EventViewType.allCases, id: \.self) { viewType in
                Button(action: { switchView(viewType) }) {
                    Text(viewType.rawValue)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .padding(.vertical, 8)
                        .padding(.horizontal, 15)
                        .background(buttonBackground(for: viewType))
                        .foregroundColor(buttonTextColor(for: viewType))
                        .cornerRadius(20)
                        .overlay(buttonBorder(for: viewType))
                }
            }
        }
    }
    
    private func buttonBackground(for viewType: EventViewType) -> Color {
        currentView == viewType ? Color(hex: "4facfe") : Color.clear
    }
    
    private func buttonTextColor(for viewType: EventViewType) -> Color {
        currentView == viewType ? .white : Color(hex: "A0A0A0")
    }
    
    private func buttonBorder(for viewType: EventViewType) -> some View {
        RoundedRectangle(cornerRadius: 20)
            .stroke(currentView == viewType ? Color(hex: "4facfe") : Color(hex: "303030"), lineWidth: 1)
    }
    
    private var headerBackground: some View {
        Color.black.opacity(0.85)
            .background(.ultraThinMaterial)
            .edgesIgnoringSafeArea(.top)
    }
    
    private var headerBorder: some View {
        Rectangle()
            .frame(height: 1)
            .foregroundColor(Color(hex: "303030"))
    }
    
    private var controlsView: some View {
        FilterView(
            searchTerm: $searchTerm,
            yearFilter: $yearFilter,
            statusFilter: $statusFilter,
            availableYears: availableYears,
            onFilterChanged: filterEvents
        )
    }
    
    private var loadingView: some View {
        VStack {
            ProgressView()
                .progressViewStyle(CircularProgressViewStyle(tint: Color(hex: "4facfe")))
                .scaleEffect(1.5)
            Text("Loading events...")
                .foregroundColor(.gray)
                .padding(.top, 10)
        }
        .padding(.vertical, 50)
        .frame(maxWidth: .infinity)
        .background(Color(hex: "1A1A1A").opacity(0.7))
        .cornerRadius(20)
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(Color(hex: "303030"), lineWidth: 1)
        )
    }
    
    private var noResultsView: some View {
        VStack {
            Image(systemName: "magnifyingglass")
                .font(.largeTitle)
                .foregroundColor(.gray)
            Text("No events found matching your criteria.")
                .foregroundColor(.gray)
                .padding(.top, 10)
        }
        .padding(.vertical, 50)
        .frame(maxWidth: .infinity)
        .background(Color(hex: "1A1A1A").opacity(0.7))
        .cornerRadius(20)
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(Color(hex: "303030"), lineWidth: 1)
        )
    }
    
    private func errorView(message: String) -> some View {
        VStack {
            Image(systemName: "exclamationmark.triangle")
                .font(.largeTitle)
                .foregroundColor(.red)
            Text("Error loading events")
                .font(.headline)
                .foregroundColor(.white)
                .padding(.top, 10)
            Text(message)
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            Button("Retry") {
                loadEvents()
            }
            .padding()
            .background(Color(hex: "4facfe"))
            .foregroundColor(.white)
            .cornerRadius(8)
            .padding(.top, 10)
        }
        .padding(.vertical, 50)
        .frame(maxWidth: .infinity)
        .background(Color(hex: "1A1A1A").opacity(0.7))
        .cornerRadius(20)
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(Color(hex: "303030"), lineWidth: 1)
        )
    }
    
    private var eventsGridView: some View {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 350), spacing: 20)], spacing: 20) {
            ForEach(filteredEvents) { event in
                NavigationLink(destination: EventDetailView(event: event)) {
                    EventCardView(event: event)
                }
                .buttonStyle(PlainButtonStyle()) // To remove default NavigationLink styling
                .onAppear {
                    // Trigger loading more events when approaching the end
                    if currentView == .recent && event == filteredEvents.last && hasMorePages && !isLoadingMore {
                        loadMoreEvents()
                    }
                }
            }
            
            // Show loading indicator at bottom for pagination
            if currentView == .recent && isLoadingMore {
                VStack {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: Color(hex: "4facfe")))
                        .scaleEffect(1.2)
                    Text("Loading more events...")
                        .foregroundColor(.gray)
                        .font(.caption)
                        .padding(.top, 5)
                }
                .padding(.vertical, 20)
                .frame(maxWidth: .infinity)
            }
        }
    }
    
    // MARK: - Data & Logic
    
    private func loadEvents() {
        isLoading = true
        errorMessage = nil
        currentPage = 1
        hasMorePages = true
        
        Task {
            do {
                let fetchedEvents: [UFCEvent]
                
                switch currentView {
                case .upcoming:
                    fetchedEvents = try await networkService.fetchUpcomingEvents()
                    await MainActor.run {
                        self.events = fetchedEvents
                        self.hasMorePages = false // Upcoming events don't use pagination
                    }
                case .recent:
                    let response = try await networkService.fetchHistoricalEvents(page: 1, limit: 20)
                    await MainActor.run {
                        self.events = response.events
                        self.hasMorePages = response.pagination.hasNext
                        self.currentPage = 1
                    }
                }
                
                await MainActor.run {
                    print("📱 Received \(self.events.count) events for \(currentView.rawValue)")
                    for event in self.events.prefix(3) {
                        print("  - \(event.eventName) on \(event.eventDate)")
                    }
                    
                    self.populateYearFilter()
                    self.filterEvents()
                    
                    print("📱 After filtering: \(filteredEvents.count) events")
                    for event in filteredEvents.prefix(3) {
                        print("  - \(event.eventName) on \(event.eventDate)")
                    }
                    
                    self.isLoading = false
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.events = UFCEvent.sampleData // Fallback to sample data
                    self.populateYearFilter()
                    self.filterEvents()
                    self.isLoading = false
                }
            }
        }
    }
    
    private func loadMoreEvents() {
        guard currentView == .recent && hasMorePages && !isLoadingMore else { return }
        
        isLoadingMore = true
        let nextPage = currentPage + 1
        
        Task {
            do {
                let response = try await networkService.fetchHistoricalEvents(page: nextPage, limit: 20)
                
                await MainActor.run {
                    print("📱 Loaded page \(nextPage) with \(response.events.count) more events")
                    
                    self.events.append(contentsOf: response.events)
                    self.hasMorePages = response.pagination.hasNext
                    self.currentPage = nextPage
                    
                    self.populateYearFilter()
                    self.filterEvents()
                    self.isLoadingMore = false
                }
            } catch {
                await MainActor.run {
                    print("📱 Failed to load more events: \(error.localizedDescription)")
                    self.isLoadingMore = false
                }
            }
        }
    }
    
    private func populateYearFilter() {
        let years = Set(events.map { Calendar.current.component(.year, from: $0.eventDate) })
        availableYears = years.map { String($0) }.sorted(by: >)
    }
    
    private func switchView(_ viewType: EventViewType) {
        currentView = viewType
        loadEvents() // Reload data when switching views
    }
    
    private func filterEvents() {
        var filtered = events
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: Date())
        
        // Apply view-specific filters
        switch currentView {
        case .upcoming:
            filtered = filtered.filter { event in
                let eventStartOfDay = calendar.startOfDay(for: event.eventDate)
                return eventStartOfDay >= today
            }
            filtered.sort { $0.eventDate < $1.eventDate }
        case .recent:
            filtered = filtered.filter { event in
                let eventStartOfDay = calendar.startOfDay(for: event.eventDate)
                return eventStartOfDay < today
            }
            filtered.sort { $0.eventDate > $1.eventDate }
        }
        
        // Filter by search term
        if !searchTerm.isEmpty {
            filtered = filtered.filter { event in
                event.eventName.localizedCaseInsensitiveContains(searchTerm) ||
                (event.venue?.localizedCaseInsensitiveContains(searchTerm) ?? false) ||
                (event.location?.localizedCaseInsensitiveContains(searchTerm) ?? false) ||
                event.fights.contains(where: { fight in
                    fight.fighter1.name.localizedCaseInsensitiveContains(searchTerm) ||
                    fight.fighter2.name.localizedCaseInsensitiveContains(searchTerm)
                })
            }
        }
        
        // Filter by year
        if !yearFilter.isEmpty {
            filtered = filtered.filter { Calendar.current.component(.year, from: $0.eventDate).description == yearFilter }
        }
        
        // Filter by status
        if !statusFilter.isEmpty {
            filtered = filtered.filter { $0.status.rawValue == statusFilter }
        }
        
        self.filteredEvents = filtered
    }
}

// MARK: - Helper Extensions

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (1, 1, 1, 0) // Fallback to clear
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

enum EventViewType: String, CaseIterable {
    case upcoming = "Upcoming"
    case recent = "Recent"
}

struct EventListView_Previews: PreviewProvider {
    static var previews: some View {
        EventListView()
            .preferredColorScheme(.dark)
    }
}