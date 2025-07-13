import SwiftUI

struct FilterView: View {
    @Binding var searchTerm: String
    @Binding var yearFilter: String
    @Binding var statusFilter: String
    let availableYears: [String]
    let onFilterChanged: () -> Void
    
    var body: some View {
        VStack(spacing: 20) {
            searchSection
            filterPickersSection
        }
        .padding(20)
        .background(filterBackground)
        .cornerRadius(20)
        .shadow(color: Color.black.opacity(0.3), radius: 15, x: 0, y: 10)
    }
    
    // MARK: - Search Section
    
    private var searchSection: some View {
        HStack(spacing: 12) {
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(Color(hex: "4facfe"))
                    .font(.system(size: 16, weight: .medium))
                
                TextField("Search events or fighters...", text: $searchTerm)
                    .foregroundColor(.white)
                    .accentColor(Color(hex: "4facfe"))
                    .onChange(of: searchTerm) { _ in
                        onFilterChanged()
                    }
                
                if !searchTerm.isEmpty {
                    Button(action: {
                        searchTerm = ""
                        onFilterChanged()
                    }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(Color(hex: "A0A0A0"))
                            .font(.system(size: 16))
                    }
                }
            }
            .padding(.horizontal, 15)
            .padding(.vertical, 12)
            .background(searchInputBackground)
            .cornerRadius(12)
            
            searchButton
        }
    }
    
    private var searchInputBackground: some View {
        RoundedRectangle(cornerRadius: 12)
            .fill(Color(hex: "1A1A1A"))
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(
                        searchTerm.isEmpty ? Color(hex: "303030") : Color(hex: "4facfe"),
                        lineWidth: 1
                    )
            )
    }
    
    private var searchButton: some View {
        Button(action: {
            onFilterChanged()
        }) {
            Text("Search")
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundColor(.white)
                .padding(.horizontal, 20)
                .padding(.vertical, 12)
                .background(searchButtonBackground)
                .cornerRadius(12)
        }
    }
    
    private var searchButtonBackground: some View {
        RoundedRectangle(cornerRadius: 12)
            .fill(
                LinearGradient(
                    gradient: Gradient(colors: [Color(hex: "4facfe"), Color(hex: "00f2fe")]),
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .shadow(color: Color(hex: "4facfe").opacity(0.25), radius: 8, x: 0, y: 4)
    }
    
    // MARK: - Filter Pickers Section
    
    private var filterPickersSection: some View {
        HStack(spacing: 15) {
            yearFilterPicker
            statusFilterPicker
        }
    }
    
    private var yearFilterPicker: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Year")
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(Color(hex: "A0A0A0"))
                .textCase(.uppercase)
            
            Menu {
                Button("All Years") {
                    yearFilter = ""
                    onFilterChanged()
                }
                .foregroundColor(yearFilter.isEmpty ? Color(hex: "4facfe") : .primary)
                
                ForEach(availableYears, id: \.self) { year in
                    Button(year) {
                        yearFilter = year
                        onFilterChanged()
                    }
                    .foregroundColor(yearFilter == year ? Color(hex: "4facfe") : .primary)
                }
            } label: {
                HStack {
                    Text(yearFilter.isEmpty ? "All Years" : yearFilter)
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(.white)
                    
                    Spacer()
                    
                    Image(systemName: "chevron.down")
                        .font(.caption)
                        .foregroundColor(Color(hex: "4facfe"))
                }
                .padding(.horizontal, 15)
                .padding(.vertical, 12)
                .background(pickerBackground)
                .cornerRadius(12)
            }
        }
        .frame(maxWidth: .infinity)
    }
    
    private var statusFilterPicker: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Status")
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(Color(hex: "A0A0A0"))
                .textCase(.uppercase)
            
            Menu {
                Button("All Statuses") {
                    statusFilter = ""
                    onFilterChanged()
                }
                .foregroundColor(statusFilter.isEmpty ? Color(hex: "4facfe") : .primary)
                
                ForEach(EventStatus.allCases, id: \.self) { status in
                    Button(status.displayName) {
                        statusFilter = status.rawValue
                        onFilterChanged()
                    }
                    .foregroundColor(statusFilter == status.rawValue ? Color(hex: "4facfe") : .primary)
                }
            } label: {
                HStack {
                    Text(statusDisplayName)
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(.white)
                    
                    Spacer()
                    
                    Image(systemName: "chevron.down")
                        .font(.caption)
                        .foregroundColor(Color(hex: "4facfe"))
                }
                .padding(.horizontal, 15)
                .padding(.vertical, 12)
                .background(pickerBackground)
                .cornerRadius(12)
            }
        }
        .frame(maxWidth: .infinity)
    }
    
    private var statusDisplayName: String {
        if statusFilter.isEmpty {
            return "All Statuses"
        }
        return EventStatus(rawValue: statusFilter)?.displayName ?? "All Statuses"
    }
    
    private var pickerBackground: some View {
        RoundedRectangle(cornerRadius: 12)
            .fill(Color(hex: "1A1A1A"))
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(Color(hex: "303030"), lineWidth: 1)
            )
    }
    
    private var filterBackground: some View {
        RoundedRectangle(cornerRadius: 20)
            .fill(Color(hex: "1A1A1A").opacity(0.7))
            .background(.ultraThinMaterial)
            .overlay(
                RoundedRectangle(cornerRadius: 20)
                    .stroke(Color(hex: "303030"), lineWidth: 1)
            )
    }
}

// MARK: - Preview
struct FilterView_Previews: PreviewProvider {
    static var previews: some View {
        VStack {
            FilterView(
                searchTerm: .constant(""),
                yearFilter: .constant(""),
                statusFilter: .constant(""),
                availableYears: ["2025", "2024", "2023"],
                onFilterChanged: {}
            )
            
            Spacer()
        }
        .padding()
        .background(Color.black)
        .preferredColorScheme(.dark)
    }
}