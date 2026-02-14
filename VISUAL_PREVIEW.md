# 📱 Airport-Style Flight Monitor UI - Visual Preview

## What It Looks Like

The implementation creates a professional airport-style flight monitor display inspired by the reference image provided in the issue:

### Reference Airport Monitor (From Issue)
![Reference](https://github.com/user-attachments/assets/95d428b5-e6a8-4115-87cb-34446b1100d9)

## Our TypeScript Implementation

### Main Components Layout

```
┌────────────────────────────────────────────────────────────┐
│  [Switch to Departures]  [Theme: Airport Purple]           │ ← Control Buttons
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Arrivals                        Feb 14, 2026    20:30     │ ← Header
│  15 flights                                                 │
│                                                             │
├────────────────────────────────────────────────────────────┤
│ TIME   │ FLIGHT    │ ROUTE           │ STATUS  │ ALT │ SPD │ ← Column Headers
├────────────────────────────────────────────────────────────┤
│ 14:45  │ AA PS9159 │ DME → ORD      │ Arrived │ 35k │ 450 │
│ 14:50  │ BA BA0882 │ LHR → ORD      │ Arrived │ 33k │ 445 │
│ 15:00  │ DL QU4434 │ SIN → ORD      │ Landed  │  0k │  85 │
│ 15:10  │ UA OV0311 │ IST → ORD      │ Landed  │  0k │  42 │
│ 15:55  │ AA SU1800 │ DME → ORD      │ In Flight│ 38k │ 485 │
│ 16:25  │ LH LH2544 │ FRA → ORD      │ Delayed │ 32k │ 430 │
│ 16:30  │ TK TK0455 │ IST → ORD      │ Boarding│  0k │   0 │
│ 16:50  │ AF AF1252 │ CDG → ORD      │ Scheduled│  0k │   0 │
│ 16:50  │ DL DL8518 │ CDG → ORD      │ Scheduled│  0k │   0 │
│ ...                                                         │
└────────────────────────────────────────────────────────────┘
     ↑         ↑          ↑              ↑         ↑     ↑
   Time    Airline    Origin→Dest     Status    Alt  Speed
           Badge
```

### Color Coding

**Status Colors:**
- 🟢 **Green** (`success`) - Arrived, Landed
- 🔴 **Red** (`error`) - Cancelled, Delayed
- 🟡 **Yellow** (`warning`) - Boarding
- ⚪ **White** (`text`) - Scheduled, In Flight

### Theme Examples

#### 1. Airport Purple (Default)
```
Background: #1A0B2E (very dark purple)
Primary: #9D4EDD (bright purple)
Surface: #2E1A47 (dark purple)
Text: #FFFFFF (white)
```

#### 2. Airport Blue
```
Background: #001F3F (navy blue)
Primary: #0096FF (bright blue)
Surface: #003366 (dark blue)
Text: #FFFFFF (white)
```

#### 3. Airport Green
```
Background: #064E3B (dark green)
Primary: #10B981 (bright green)
Surface: #065F46 (darker green)
Text: #FFFFFF (white)
```

#### 4. Dark Mode
```
Background: #121212 (very dark gray)
Primary: #2196F3 (blue)
Surface: #1E1E1E (dark gray)
Text: #FFFFFF (white)
```

#### 5. Light Mode
```
Background: #F5F5F5 (light gray)
Primary: #1976D2 (blue)
Surface: #FFFFFF (white)
Text: #212121 (dark text)
```

## Component Breakdown

### 1. Control Buttons (Top Bar)
```typescript
┌─────────────────────────────────────────┐
│  [Switch to Departures]  [Theme: ...]  │
└─────────────────────────────────────────┘
```
- **Left Button**: Toggle between Arrivals/Departures
- **Right Button**: Cycle through 5 themes
- Background: `surface` color
- Button color: `primary` and `secondary`

### 2. Header Banner
```typescript
┌─────────────────────────────────────────┐
│  Arrivals              Feb 14, 2026     │
│  15 flights            20:30            │
└─────────────────────────────────────────┘
```
- Background: `primary` color
- Text: White/`text` color
- Updates: Clock updates every minute
- Shows: View type + flight count + current date/time

### 3. Column Headers
```typescript
┌────────────────────────────────────────┐
│ TIME │ FLIGHT │ ROUTE │ STATUS │ ...   │
└────────────────────────────────────────┘
```
- Background: `surface` color
- Border: `border` color
- Text: `text` color
- Font: Bold, uppercase, monospace

### 4. Flight Rows
```typescript
┌─────────────────────────────────────────────────┐
│ 14:45 │ AA │ PS9159 │ DME → ORD │ Arrived │ ... │
└─────────────────────────────────────────────────┘
```
Each row contains:

**Time Column** (80px):
- Departure/arrival time
- Format: HH:MM (24-hour)
- Font: Bold, monospace

**Flight Column** (120px):
- Airline badge (colored box with IATA code)
- Flight number
- Font: Bold, monospace

**Route Column** (flex):
- Origin IATA code
- Arrow (→)
- Destination IATA code
- Font: Semi-bold

**Status Column** (120px):
- Status text (Arrived, Delayed, etc.)
- Color-coded by status
- Font: Bold, uppercase

**Altitude Column** (90px):
- Altitude in thousands of feet (e.g., "35k ft")
- Label: "ALT"
- Font: Monospace

**Speed Column** (90px):
- Speed in knots (e.g., "450 kts")
- Label: "SPD"
- Font: Monospace

## Responsive Behavior

### Phone (Portrait)
```
┌──────────────┐
│  Buttons     │
├──────────────┤
│  Header      │
├──────────────┤
│ T│FL│Route  │ ← Condensed columns
├──────────────┤
│ 14:45│AA1234│
│      │ORD→LAX│
│      │Arrived│ ← Wrapped info
├──────────────┤
│ ...          │
└──────────────┘
```

### Tablet/Desktop
```
┌────────────────────────────────────────┐
│          Buttons                       │
├────────────────────────────────────────┤
│               Header                   │
├────────────────────────────────────────┤
│ TIME │ FLIGHT │ ROUTE │ STATUS │ ... │ ← All columns
├────────────────────────────────────────┤
│ 14:45│AA PS9159│DME→ORD│Arrived│35k│450│
│ 14:50│BA BA0882│LHR→ORD│Arrived│33k│445│
│ ...                                     │
└────────────────────────────────────────┘
```

## Interactive Features

### Pull to Refresh
```
    ↓ Pull down ↓
┌─────────────────┐
│   🔄 Loading... │
└─────────────────┘
```
- Swipe down to refresh flight data
- Shows loading indicator
- Updates flight list

### Scrolling
```
┌─────────────────┐
│ Flight 1        │ ← Visible
│ Flight 2        │
│ Flight 3        │
├─────────────────┤
│ Flight 4        │ ← Scroll to see
│ Flight 5        │
│ ...             │
└─────────────────┘
```
- Smooth scrolling
- Fixed header
- Infinite scroll for many flights

### Real-Time Updates
```
Before:          After 5 seconds:
Altitude: 35k ft → Altitude: 36k ft
Speed: 450 kts   → Speed: 455 kts
Status: In Flight → Status: In Flight
```
- Auto-updates every 5 seconds
- Smooth transitions
- No page reload

## Typography

**Fonts Used:**
- **Headers**: System font, bold
- **Time**: Monospace, bold, 18px
- **Flight Number**: Monospace, bold, 16px
- **Route**: System font, semi-bold, 16px
- **Status**: System font, bold, 14px, uppercase
- **Data (Alt/Speed)**: Monospace, semi-bold, 14px

## Accessibility

- ✅ High contrast text (WCAG AA compliant)
- ✅ Large touch targets (44x44px minimum)
- ✅ Clear visual hierarchy
- ✅ Readable fonts at all sizes
- ✅ Color + text for status (not color alone)

## Animation (Future Enhancement)

### Status Change
```
Before: [Scheduled]
   ↓    Fade transition
After:  [Boarding]
```

### New Flight
```
[New flight slides in from top]
↓
[Existing flights shift down]
```

### Flight Removal
```
[Flight fades out]
↓
[Other flights shift up]
```

## Example Flight Data Display

### Arrival Example
```typescript
{
  time: "14:45",
  airline: "AA",
  flightNumber: "PS9159",
  from: "DME",        // Moscow
  to: "ORD",          // Chicago
  status: "Arrived",  // Green
  altitude: "35k ft",
  speed: "450 kts"
}
```

Displays as:
```
14:45  │ AA  PS9159 │ DME → ORD │ Arrived │ 35k ft │ 450 kts
       │ ^          │           │   ^     │
       └─ Purple    └─ Bold     └── Green
          badge        text         text
```

### Departure Example
```typescript
{
  time: "16:30",
  airline: "TK",
  flightNumber: "TK0455",
  from: "ORD",        // Chicago
  to: "IST",          // Istanbul
  status: "Boarding", // Yellow
  altitude: "0k ft",  // On ground
  speed: "0 kts"      // Not moving
}
```

Displays as:
```
16:30  │ TK  TK0455 │ ORD → IST │ Boarding │ 0k ft │ 0 kts
       │            │           │    ^     │
       │            │           └─── Yellow
       │            │                text
```

## Empty State

When no flights:
```
┌────────────────────────┐
│                        │
│                        │
│   No flights to        │
│   display              │
│                        │
│                        │
└────────────────────────┘
```

## Loading State

Initial load:
```
┌────────────────────────┐
│        🔄              │
│     Loading            │
│     flights...         │
└────────────────────────┘
```

## Technical Implementation

All components built with **TypeScript** for type safety:

```typescript
// Strongly typed props
interface FlightRowProps {
  flight: Flight;      // Full type checking
  theme: Theme;        // Theme type
  showAirline?: boolean;
  showStatus?: boolean;
}

// Type-safe component
const FlightRow: React.FC<FlightRowProps> = ({
  flight,
  theme,
  showAirline = true,
  showStatus = true,
}) => {
  // Render flight row
};
```

## Summary

The TypeScript implementation creates a:

✅ **Professional airport monitor display**  
✅ **5 customizable color themes**  
✅ **Responsive mobile-first design**  
✅ **Real-time flight updates**  
✅ **Type-safe React Native components**  
✅ **Clear visual hierarchy**  
✅ **Accessible interface**

Ready to deploy to: **https://github.com/jromie0924/plane-tracker-monitor-ui**

---

**All components are TypeScript with full type safety! 💪**
