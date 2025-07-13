// UFC Events Dashboard JavaScript

class UFCDashboard {
    constructor() {
        this.events = [];
        this.filteredEvents = [];
        this.currentView = 'all';
        this.searchTerm = '';
        this.yearFilter = '';
        this.statusFilter = '';
        
        this.init();
    }

    init() {
        this.loadEvents();
        this.setupEventListeners();
        this.populateYearFilter();
    }

    setupEventListeners() {
        // Navigation buttons
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchView(e.target.dataset.view);
            });
        });

        // Search functionality
        const searchInput = document.getElementById('search-input');
        const searchBtn = document.getElementById('search-btn');
        
        searchInput.addEventListener('input', (e) => {
            this.searchTerm = e.target.value.toLowerCase();
            this.filterEvents();
        });

        searchBtn.addEventListener('click', () => {
            this.filterEvents();
        });

        // Filters
        document.getElementById('year-filter').addEventListener('change', (e) => {
            this.yearFilter = e.target.value;
            this.filterEvents();
        });

        document.getElementById('status-filter').addEventListener('change', (e) => {
            this.statusFilter = e.target.value;
            this.filterEvents();
        });

        // Modal
        document.getElementById('modal-close').addEventListener('click', () => {
            this.closeModal();
        });

        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal();
            }
        });
    }

    async loadEvents() {
        try {
            this.showLoading(true);
            console.log("Attempting to load events...");
            
            // Try to load from API first
            try {
                const response = await fetch('/api/events');
                if (response.ok) {
                    this.events = await response.json();
                    console.log("Events loaded from API:", this.events.length);
                    this.populateYearFilter(); // Populate years after loading events
                    this.filterEvents();
                    return;
                }
            } catch (apiError) {
                console.error('API not available, using sample data:', apiError);
            }
            
            // Load sample data as fallback
            this.events = this.getSampleData();
            console.log("Events loaded from sample data:", this.events.length);
            this.populateYearFilter();
            this.filterEvents();
            
        } catch (error) {
            console.error('Error loading events:', error);
            // Load sample data as fallback
            this.events = this.getSampleData();
            this.populateYearFilter();
            this.filterEvents();
        } finally {
            this.showLoading(false);
            console.log("Loading complete.");
        }
    }

    populateYearFilter() {
        console.log("Populating year filter...");
        const yearFilterSelect = document.getElementById('year-filter');
        const years = new Set();
        this.events.forEach(event => {
            const year = new Date(event.event_date).getFullYear();
            years.add(year);
        });

        // Clear existing options except "All Years"
        yearFilterSelect.innerHTML = '<option value="">All Years</option>';

        // Add years in descending order
        Array.from(years).sort((a, b) => b - a).forEach(year => {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            yearFilterSelect.appendChild(option);
        });
        console.log("Year filter populated with years:", Array.from(years).sort((a, b) => b - a));
    }

    getSampleData() {
        // Sample UFC event data for demonstration
        return [
            {
                event_id: "ufc-305",
                event_name: "UFC 305: Du Plessis vs Adesanya",
                event_date: "2024-08-17",
                venue: "RAC Arena",
                location: "Perth, Australia",
                status: "completed",
                fights: [
                    {
                        bout_order: 1,
                        fighter1: {
                            name: "Dricus du Plessis",
                            record: "22-2-0",
                            rank: 1,
                            country: "South Africa"
                        },
                        fighter2: {
                            name: "Israel Adesanya",
                            record: "24-3-0",
                            rank: 2,
                            country: "Nigeria"
                        },
                        weight_class: "Middleweight Championship",
                        title_fight: "undisputed",
                        method: "Submission (R4 3:38)",
                        winner: "Dricus du Plessis"
                    },
                    {
                        bout_order: 2,
                        fighter1: {
                            name: "Kai Kara-France",
                            record: "24-11-0",
                            country: "New Zealand"
                        },
                        fighter2: {
                            name: "Steve Erceg",
                            record: "12-2-0",
                            country: "Australia"
                        },
                        weight_class: "Flyweight",
                        title_fight: "none",
                        method: "Decision (Unanimous)",
                        winner: "Kai Kara-France"
                    }
                ]
            },
            {
                event_id: "ufc-306",
                event_name: "UFC 306: O'Malley vs Dvalishvili",
                event_date: "2024-09-14",
                venue: "The Sphere",
                location: "Las Vegas, NV",
                status: "completed",
                fights: [
                    {
                        bout_order: 1,
                        fighter1: {
                            name: "Sean O'Malley",
                            record: "18-2-0",
                            rank: 1,
                            country: "USA"
                        },
                        fighter2: {
                            name: "Merab Dvalishvili",
                            record: "17-4-0",
                            rank: 2,
                            country: "Georgia"
                        },
                        weight_class: "Bantamweight Championship",
                        title_fight: "undisputed",
                        method: "Decision (Unanimous)",
                        winner: "Merab Dvalishvili"
                    }
                ]
            },
            {
                event_id: "ufc-310",
                event_name: "UFC 310: Pantoja vs Asakura",
                event_date: "2024-12-07",
                venue: "T-Mobile Arena",
                location: "Las Vegas, NV",
                status: "completed",
                fights: [
                    {
                        bout_order: 1,
                        fighter1: {
                            name: "Alexandre Pantoja",
                            record: "28-5-0",
                            rank: 1,
                            country: "Brazil"
                        },
                        fighter2: {
                            name: "Kai Asakura",
                            record: "21-4-0",
                            country: "Japan"
                        },
                        weight_class: "Flyweight Championship",
                        title_fight: "undisputed",
                        method: "Decision (Unanimous)",
                        winner: "Alexandre Pantoja"
                    }
                ]
            },
            {
                event_id: "ufc-311",
                event_name: "UFC 311: Makhachev vs Moicano",
                event_date: "2025-01-18",
                venue: "Intuit Dome",
                location: "Inglewood, CA",
                status: "scheduled",
                fights: [
                    {
                        bout_order: 1,
                        fighter1: {
                            name: "Islam Makhachev",
                            record: "26-1-0",
                            rank: 1,
                            country: "Russia"
                        },
                        fighter2: {
                            name: "Renato Moicano",
                            record: "19-5-1",
                            rank: 4,
                            country: "Brazil"
                        },
                        weight_class: "Lightweight Championship",
                        title_fight: "undisputed"
                    },
                    {
                        bout_order: 2,
                        fighter1: {
                            name: "Merab Dvalishvili",
                            record: "18-4-0",
                            rank: 1,
                            country: "Georgia"
                        },
                        fighter2: {
                            name: "Umar Nurmagomedov",
                            record: "18-0-0",
                            rank: 2,
                            country: "Russia"
                        },
                        weight_class: "Bantamweight Championship",
                        title_fight: "undisputed"
                    }
                ]
            },
            {
                event_id: "ufc-312",
                event_name: "UFC 312",
                event_date: "2025-02-08",
                venue: "Qudos Bank Arena",
                location: "Sydney, Australia",
                status: "scheduled",
                fights: [
                    {
                        bout_order: 1,
                        fighter1: {
                            name: "Jon Jones",
                            record: "27-1-0",
                            rank: 1,
                            country: "USA"
                        },
                        fighter2: {
                            name: "Tom Aspinall",
                            record: "15-3-0",
                            rank: 1,
                            country: "England"
                        },
                        weight_class: "Heavyweight Championship",
                        title_fight: "undisputed"
                    }
                ]
            }
        ];
    }

    switchView(view) {
        console.log("Switching view to:", view);
        this.currentView = view;
        
        // Update active nav button
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-view="${view}"]`).classList.add('active');
        
        this.filterEvents();
    }

    filterEvents() {
        console.log("Filtering events... Initial events count:", this.events.length);
        const now = new Date();
        let filtered = [...this.events];

        // Apply view-specific filters first
        if (this.currentView === 'upcoming') {
            filtered = filtered.filter(event => new Date(event.event_date) >= now);
            // Sort upcoming events by date ascending
            filtered.sort((a, b) => new Date(a.event_date) - new Date(b.event_date));
            console.log("After 'upcoming' filter, count:", filtered.length);
        } else if (this.currentView === 'recent') {
            filtered = filtered.filter(event => new Date(event.event_date) < now);
            // Sort recent events by date descending
            filtered.sort((a, b) => new Date(b.event_date) - new Date(a.event_date));
            filtered = filtered.slice(0, 10); // Show only recent 10
            console.log("After 'recent' filter, count:", filtered.length);
        } else if (this.currentView === 'all') {
            // For 'all' view, sort by date descending by default
            filtered.sort((a, b) => new Date(b.event_date) - new Date(a.event_date));
            console.log("After 'all' view sort, count:", filtered.length);
        }

        // Filter by search term
        if (this.searchTerm) {
            filtered = filtered.filter(event => 
                event.event_name.toLowerCase().includes(this.searchTerm) ||
                event.venue?.toLowerCase().includes(this.searchTerm) ||
                event.location?.toLowerCase().includes(this.searchTerm) ||
                event.fights.some(fight => 
                    fight.fighter1.name.toLowerCase().includes(this.searchTerm) ||
                    fight.fighter2.name.toLowerCase().includes(this.searchTerm)
                )
            );
            console.log("After search term filter, count:", filtered.length);
        }

        // Filter by year
        if (this.yearFilter) {
            filtered = filtered.filter(event => 
                new Date(event.event_date).getFullYear().toString() === this.yearFilter
            );
            console.log("After year filter, count:", filtered.length);
        }

        // Filter by status
        if (this.statusFilter) {
            filtered = filtered.filter(event => event.status === this.statusFilter);
            console.log("After status filter, count:", filtered.length);
        }

        this.filteredEvents = filtered;
        console.log("Final filtered events count:", this.filteredEvents.length);
        this.renderEvents();
    }

    renderEvents() {
        try {
            console.log("Rendering events...");
            const grid = document.getElementById('events-grid');
            const noResults = document.getElementById('no-results');

            if (this.filteredEvents.length === 0) {
                grid.innerHTML = '';
                noResults.style.display = 'block';
                console.log("No filtered events to render.");
                return;
            }

            noResults.style.display = 'none';
            grid.innerHTML = this.filteredEvents.map((event, index) => {
                const card = this.createEventCard(event);
                return card.replace('<div class="event-card"', `<div class="event-card" style="--animation-delay: ${index}"`);
            }).join('');
            console.log("Events rendered to grid.");

            // Add click listeners to event cards
            document.querySelectorAll('.event-card').forEach(card => {
                card.addEventListener('click', () => {
                    const eventId = card.dataset.eventId;
                    this.showEventDetails(eventId);
                });
            });
            console.log("Event card click listeners added.");
        } catch (e) {
            console.error("Error during renderEvents:", e);
        }
    }

    createEventCard(event) {
        console.log("Creating event card for:", event.event_name);
        const sortedFights = this.getSortedFights(event);
        const mainEvent = sortedFights[0]; // Main event is always the first fight (highest bout_order overall)
        const eventDate = new Date(event.event_date);
        const isUpcoming = eventDate >= new Date();
        
        return `
            <div class="event-card" data-event-id="${event.event_id}">
                <div class="hover-cta">👆 CLICK TO VIEW</div>
                <div class="event-header">
                    <div>
                        <h3 class="event-title">${event.event_name}</h3>
                        <p class="event-date">${this.formatDate(event.event_date)}</p>
                    </div>
                    <span class="event-status ${event.status}">${event.status}</span>
                </div>
                
                <div class="event-venue">
                    ${event.venue || ''} ${event.location ? `• ${event.location}` : ''}
                </div>
                
                ${mainEvent ? `
                    <div class="main-event">
                        <div class="main-event-title">Main Event</div>
                        <div class="fighters">
                            <div class="fighter">
                                <div class="fighter-name">${mainEvent.fighter1.name}</div>
                                ${mainEvent.fighter1.record ? `<div class="fighter-record">${mainEvent.fighter1.record}</div>` : ''}
                            </div>
                            <div class="vs">VS</div>
                            <div class="fighter">
                                <div class="fighter-name">${mainEvent.fighter2.name}</div>
                                ${mainEvent.fighter2.record ? `<div class="fighter-record">${mainEvent.fighter2.record}</div>` : ''}
                            </div>
                        </div>
                        <div class="weight-class ${mainEvent.title_fight !== 'none' ? 'title-fight' : ''}">
                            ${mainEvent.weight_class}
                            ${mainEvent.title_fight !== 'none' ? ' 🏆' : ''}
                        </div>
                        ${mainEvent.winner && !isUpcoming ? `
                            <div class="fight-result">
                                <div class="winner">Winner: ${mainEvent.winner}</div>
                                ${mainEvent.method ? `<div class="method">${mainEvent.method}</div>` : ''}
                            </div>
                        ` : ''}
                    </div>
                ` : ''}
                
                <div class="fight-count">
                    ${event.fights.length} fight${event.fights.length !== 1 ? 's' : ''} on card
                </div>
            </div>
        `;
    }

    showEventDetails(eventId) {
        console.log("Showing details for event:", eventId);
        const event = this.events.find(e => e.event_id === eventId);
        if (!event) {
            console.warn("Event not found:", eventId);
            return;
        }

        const modal = document.getElementById('event-modal');
        const modalBody = document.getElementById('modal-body');

        const sortedFights = this.getSortedFights(event);

        modalBody.innerHTML = `
            <div class="modal-header">
                <h2 class="modal-title">${event.event_name}</h2>
                <p class="modal-subtitle">
                    ${this.formatDate(event.event_date)} • ${event.venue || ''} ${event.location ? `• ${event.location}` : ''}
                </p>
            </div>
            <div class="modal-body">
                <h3 class="segment-title main-card-title">Fight Card</h3>
                ${this.createSegmentedFightCard(sortedFights)}
            </div>
        `;

        modal.classList.add('show'); // Use class for better control
        console.log("Modal displayed for event:", event.event_name);
    }

    createSegmentedFightCard(sortedFights) {
        console.log("Creating segmented fight card...");
        const totalFights = sortedFights.length;
        
        // First try to use scraped segment data if available
        const scrapedSegments = this.groupByScrapedSegments(sortedFights);
        if (scrapedSegments.hasSegmentData) {
            console.log("Rendering scraped segments.");
            return this.renderScrapedSegments(scrapedSegments, totalFights);
        }
        
        // Fallback to intelligent categorization
        console.log("Falling back to intelligent categorization.");
        const segments = this.categorizeFlights(sortedFights);
        
        let html = '';
        
        // Main Card
        if (segments.mainCard.length > 0) {
            html += `
                <div class="card-segment">
                    <h4 class="segment-title main-card-title">Main Card</h4>
                    ${segments.mainCard.map((fight, index) => 
                        this.createFightCard(fight, segments.mainCardStartIndex + index, totalFights)
                    ).join('')}
                </div>
            `;
        }
        
        // Prelims
        if (segments.prelims.length > 0) {
            html += `
                <div class="card-segment">
                    <h4 class="segment-title prelims-title">Preliminary Card</h4>
                    ${segments.prelims.map((fight, index) => 
                        this.createFightCard(fight, segments.prelimsStartIndex + index, totalFights)
                    ).join('')}
                </div>
            `;
        }
        
        // Early Prelims
        if (segments.earlyPrelims.length > 0) {
            html += `
                <div class="card-segment">
                    <h4 class="segment-title early-prelims-title">Early Preliminary Card</h4>
                    ${segments.earlyPrelims.map((fight, index) => 
                        this.createFightCard(fight, segments.earlyPrelimsStartIndex + index, totalFights)
                    ).join('')}
                </div>
            `;
        }
        
        return html;
    }

    groupByScrapedSegments(fights) {
        const segments = {
            'main-card': [],
            'prelims': [],
            'early-prelims': []
        };
        
        let hasSegmentData = false;
        
        for (const fight of fights) {
            if (fight.segment) {
                hasSegmentData = true;
                if (segments[fight.segment]) {
                    segments[fight.segment].push(fight);
                } else {
                    // Default to main card if unknown segment
                    segments['main-card'].push(fight);
                }
            } else {
                // No segment data, will use fallback
                break;
            }
        }
        
        return { ...segments, hasSegmentData };
    }

    renderScrapedSegments(segments, totalFights) {
        let html = '';
        let fightIndex = 0;
        
        // Main Card
        if (segments['main-card'].length > 0) {
            html += `
                <div class="card-segment">
                    <h4 class="segment-title main-card-title">Main Card <span class="segment-source">📡 Live Data</span></h4>
                    ${segments['main-card'].map((fight) => 
                        this.createFightCard(fight, fightIndex++, totalFights)
                    ).join('')}
                </div>
            `;
        }
        
        // Prelims
        if (segments['prelims'].length > 0) {
            html += `
                <div class="card-segment">
                    <h4 class="segment-title prelims-title">Preliminary Card <span class="segment-source">📡 Live Data</span></h4>
                    ${segments['prelims'].map((fight) => 
                        this.createFightCard(fight, fightIndex++, totalFights)
                    ).join('')}
                </div>
            `;
        }
        
        // Early Prelims
        if (segments['early-prelims'].length > 0) {
            html += `
                <div class="card-segment">
                    <h4 class="segment-title early-prelims-title">Early Preliminary Card <span class="segment-source">📡 Live Data</span></h4>
                    ${segments['early-prelims'].map((fight) => 
                        this.createFightCard(fight, fightIndex++, totalFights)
                    ).join('')}
                </div>
            `;
        }
        
        return html;
    }

    categorizeFlights(sortedFights) {
        const totalFights = sortedFights.length;
        
        // Analyze fight characteristics to determine segments
        const fightAnalysis = this.analyzeFightImportance(sortedFights);
        
        // Determine segments based on analysis and UFC patterns
        let mainCardSize, prelimsSize, earlyPrelimsSize;
        
        if (totalFights >= 11) {
            // PPV or big Fight Night (11+ fights)
            // Pattern: 2 early prelims, 4-5 prelims, 4-5 main card
            if (totalFights === 11) {
                earlyPrelimsSize = 2;
                prelimsSize = 5;
                mainCardSize = 4;
            } else if (totalFights === 12) {
                earlyPrelimsSize = 3;
                prelimsSize = 4;
                mainCardSize = 5;
            } else {
                earlyPrelimsSize = totalFights - 9;
                prelimsSize = 4;
                mainCardSize = 5;
            }
        } else if (totalFights >= 8) {
            // Regular Fight Night
            earlyPrelimsSize = Math.max(0, totalFights - 8);
            prelimsSize = Math.min(4, totalFights - earlyPrelimsSize - 4);
            mainCardSize = totalFights - earlyPrelimsSize - prelimsSize;
        } else {
            // Small event - all main card
            mainCardSize = totalFights;
            prelimsSize = 0;
            earlyPrelimsSize = 0;
        }
        
        // Apply adjustments based on fight analysis
        const adjustedSegments = this.adjustSegmentsByImportance(
            sortedFights, mainCardSize, prelimsSize, earlyPrelimsSize, fightAnalysis
        );
        
        return adjustedSegments;
    }
    
    analyzeFightImportance(sortedFights) {
        return sortedFights.map((fight, index) => {
            let importance = 0;
            
            // Main event gets highest importance
            if (index === 0) {
                importance += 100;
            }
            
            // Title fights are always main card
            if (fight.title_fight && fight.title_fight !== 'none') {
                importance += 50;
            }
            
            // Known main card indicators
            const fighter1Name = fight.fighter1.name.toLowerCase();
            const fighter2Name = fight.fighter2.name.toLowerCase();
            
            // High-profile fighter names (simplified list)
            const mainCardFighters = [
                'topuria', 'oliveira', 'pantoja', 'royval', 'dariush', 'moicano',
                'talbott', 'hermansson', 'rodrigues', 'cortez', 'araujo',
                'mcgregor', 'adesanya', 'jones', 'ngannou', 'usman', 'edwards',
                'poirier', 'gaethje', 'holloway', 'volkanovski', 'makhachev',
                'sterling', 'cejudo', 'figueiredo', 'moreno', 'shevchenko',
                'nunes', 'zhang', 'joanna', 'rose', 'rousey'
            ];
            
            // Check if fighters are likely main card caliber
            for (const name of mainCardFighters) {
                if (fighter1Name.includes(name) || fighter2Name.includes(name)) {
                    importance += 30;
                    break;
                }
            }
            
            // Championship weight classes tend to be more important
            const weightClass = fight.weight_class.toLowerCase();
            if (weightClass.includes('championship') || weightClass.includes('title')) {
                importance += 40;
            }
            
            // Women's fights often get featured placement
            if (weightClass.includes('women')) {
                importance += 15;
            }
            
            // Heavyweight fights often get main card treatment
            if (weightClass.includes('heavyweight')) {
                importance += 10;
            }
            
            return { fight, importance, originalIndex: index };
        });
    }
    
    adjustSegmentsByImportance(sortedFights, mainCardSize, prelimsSize, earlyPrelimsSize, analysis) {
        // Sort by importance to see if we need adjustments
        const importanceSorted = [...analysis].sort((a, b) => b.importance - a.importance);
        
        // Find fights that might be misplaced based on importance
        const highImportanceInPrelims = importanceSorted.slice(0, mainCardSize + 2)
            .filter(item => item.originalIndex >= mainCardSize);
        
        // Adjust if we find important fights in prelims
        if (highImportanceInPrelims.length > 0) {
            // Slightly increase main card size for important fights
            mainCardSize = Math.min(mainCardSize + 1, sortedFights.length - 2);
            prelimsSize = Math.max(0, prelimsSize - 1);
        }
        
        const mainCard = sortedFights.slice(0, mainCardSize);
        const prelims = sortedFights.slice(mainCardSize, mainCardSize + prelimsSize);
        const earlyPrelims = sortedFights.slice(mainCardSize + prelimsSize);
        
        return {
            mainCard,
            prelims,
            earlyPrelims,
            mainCardStartIndex: 0,
            prelimsStartIndex: mainCardSize,
            earlyPrelimsStartIndex: mainCardSize + prelimsSize
        };
    }

    getSortedFights(event) {
        const fights = [...event.fights];
        
        // Sort fights by bout_order in descending order (highest bout_order first)
        fights.sort((a, b) => b.bout_order - a.bout_order);
        
        return fights;
    }

    createFightCard(fight, displayIndex = null, totalFights = null) {
        const isMainEvent = displayIndex === 0; // First in display = main event
        const isUpcoming = !fight.winner;
        
        // Calculate the correct bout number (reverse of display order)
        let boutLabel;
        if (isMainEvent) {
            boutLabel = 'Main Event';
        } else if (displayIndex === 1) {
            boutLabel = 'Co-Main Event';
        } else if (displayIndex !== null && totalFights !== null) {
            // Bout number = total fights - display position
            const boutNumber = totalFights - displayIndex;
            boutLabel = `Bout ${boutNumber}`;
        } else {
            boutLabel = `Bout ${fight.bout_order}`;
        }
        
        return `
            <div class="fight-card ${isMainEvent ? 'main-card' : ''}">
                <div class="fight-order">
                    ${boutLabel}
                    ${fight.title_fight !== 'none' ? '<span class="title-fight-icon">🏆</span> Title Fight' : ''}
                </div>
                
                <div class="fighters">
                    <div class="fighter">
                        <div class="fighter-name ${fight.winner === fight.fighter1.name ? 'winner' : ''}">${fight.fighter1.name}</div>
                        <div class="fighter-record">${fight.fighter1.record || ''}</div>
                        ${fight.fighter1.country ? `<div class="fighter-country">${fight.fighter1.country}</div>` : ''}
                    </div>
                    <div class="vs">VS</div>
                    <div class="fighter">
                        <div class="fighter-name ${fight.winner === fight.fighter2.name ? 'winner' : ''}">${fight.fighter2.name}</div>
                        <div class="fighter-record">${fight.fighter2.record || ''}</div>
                        ${fight.fighter2.country ? `<div class="fighter-country">${fight.fighter2.country}</div>` : ''}
                    </div>
                </div>
                
                <div class="weight-class ${fight.title_fight !== 'none' ? 'title-fight' : ''}">${fight.weight_class}</div>
                
                ${fight.winner && !isUpcoming ? `
                    <div class="fight-result">
                        <div class="winner">Winner: ${fight.winner}</div>
                        ${fight.method ? `<div class="method">${fight.method}</div>` : ''}
                    </div>
                ` : ''}
            </div>
        `;
    }

    closeModal() {
        document.getElementById('event-modal').classList.remove('show');
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        const grid = document.getElementById('events-grid');
        
        if (show) {
            loading.style.display = 'block';
            grid.style.display = 'none';
        } else {
            loading.style.display = 'none';
            grid.style.display = 'grid';
        }
    }

    formatDate(dateString) {
        const options = { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        };
        return new Date(dateString).toLocaleDateString('en-US', options);
    }
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new UFCDashboard();
});