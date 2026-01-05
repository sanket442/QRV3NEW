# QR Label Generator Upgrade Plan

## Goal Description
Upgrade the existing `QRLabelGenerator` to support **dynamic label templates** (specifically a new "Folded Tag" 25x100mm) and **advanced QR settings** (Size, Error Correction), while **strictly preserving** the robust Google Sheet and CSV parsing logic.

## User Review Required
> [!IMPORTANT]
> The `@page` print size will now be dynamic. I will use a special "Print Manager" to inject the correct CSS when you switch templates.

## Proposed Changes

### Tech Stack / Libraries
- **State Management**: `zustand` (New dependency) - To handle global settings (Template, QR Size, ECC) without prop-drilling.
- **UI**: Tailwind CSS (Existing) + Lucide React (Existing).

### Refactoring Steps

#### 1. [NEW] State Store (`src/store/useLabelStore.js`)
Move "Settings" out of `QRLabelGenerator`:
- `template`: 'STANDARD' (80x20mm) or 'FOLDED' (100x25mm).
- `qrSettings`: `{ size: 20, ecc: 'H', color: '#000000' }`.
- `data`: `{ labels: [] }` (Shared state for generated labels).

#### 2. [MODIFY] `src/QRLabelGenerator.jsx` -> `src/components/LabelGenerator.jsx`
- **Keep**: `fetchSheetData`, `parseCSV`, `generateFromSheet`, `manualInput` logic.
- **Change**: 
    - Remove hardcoded render logic.
    - render `InputPanel` (Left) and `PreviewPanel` (Right).
    - Wrap in a Layout component.

#### 3. [NEW] Dynamic Print System
- **`src/components/PrintManager.jsx`**:
    - Listens to `template` state.
    - Injects a `<style>` tag with the correct `@page { size: ... }` rule.
    - Renders the "Print Grid" hidden from screen but visible to printer.

#### 4. [NEW] Templates (`src/templates/`)
- Define the geometry for:
    - **Standard**: 80mm x 20mm (Existing strict layout).
    - **Folded**: 100mm x 25mm (Fold @ 50mm, QR on right).

## Verification Plan

### Automated Tests
- Run `npm run build` to ensure no regression.

### Manual Verification
1.  **Regression Test**: Load a Google Sheet -> Generate Standard Labels -> Print. Verify 80x20mm layout matches original.
2.  **New Feature Test**: Switch to "Folded Tag".
    - Verify Screen Preview shows fold line.
    - Verify Print Preview shows 100x25mm page size.
3.  **QR Settings**: Change ECC from 'L' to 'H' and verify visual change in QR pattern.
