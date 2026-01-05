export const TEMPLATES = {
    STANDARD: {
        id: 'STANDARD',
        name: 'Standard (80x20mm)',
        width: 80,
        height: 20,
        margin: 0.1, // mm
        gap: 0.3, // mm
        description: 'Default compact label.',
        layout: 'standard'
    },
    FOLDED: {
        id: 'FOLDED',
        name: 'Folded Tag (100x25mm)',
        width: 100,
        height: 25,
        margin: 0,
        gap: 0, 
        foldLine: 50,
        description: 'Foldable tag with QR on right.',
        layout: 'folded'
    },
    TEMPLATE_1: {
        id: 'TEMPLATE_1',
        name: 'Template 1 (80x20mm)',
        width: 80,
        height: 20,
        margin: 0,
        gap: 0,
        foldLine: 40,
        description: 'Folded: 40x20mm | Printable: 3.5x1.5cm',
        layout: 'folded'
    },
    TEMPLATE_2: {
        id: 'TEMPLATE_2',
        name: 'Template 2 (100x20mm)',
        width: 100,
        height: 20,
        margin: 0,
        gap: 0,
        foldLine: 50,
        description: 'Folded: 50x20mm | Extra text support',
        layout: 'folded'
    },
    TEMPLATE_3: {
        id: 'TEMPLATE_3',
        name: 'Template 3 (60x15mm)',
        width: 60,
        height: 15,
        margin: 0,
        gap: 0,
        foldLine: 30,
        description: 'Compact Folded: 30x15mm',
        layout: 'folded'
    },
    TEMPLATE_4: {
        id: 'TEMPLATE_4',
        name: 'Template 4 (70x15mm)',
        width: 70,
        height: 15,
        margin: 0,
        gap: 0,
        foldLine: 35,
        description: 'Medium Slim Folded: 35x15mm',
        layout: 'folded'
    },
    TEMPLATE_5: {
        id: 'TEMPLATE_5',
        name: 'Template 5 (50x12mm)',
        width: 50,
        height: 12,
        margin: 0,
        gap: 0,
        foldLine: 25,
        description: 'Micro Folded: 25x12mm',
        layout: 'folded'
    }
};
