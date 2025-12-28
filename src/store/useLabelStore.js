import { create } from 'zustand';
import { TEMPLATES } from '../templates/LabelTemplates';

const useLabelStore = create((set) => ({
    // Configuration
    activeTemplate: { ...TEMPLATES.FOLDED }, // Default copy of Folded

    // QR Settings
    qrSettings: {
        size: 55, // default pixel size for 80x20 layout approx
        ecc: 'M', // Error Correction Level (15%)
        includeMargin: false,
    },

    // Actions
    setTemplate: (templateId) => set({
        activeTemplate: { ...(TEMPLATES[templateId] || TEMPLATES.FOLDED) }
    }),

    updateTemplateDimensions: (width, height, printableWidth, printableHeight, textAreaWidth, textAreaHeight, gap) => set((state) => ({
        activeTemplate: {
            ...state.activeTemplate,
            width: width ?? state.activeTemplate.width,
            height: height ?? state.activeTemplate.height,
            textAreaWidth: textAreaWidth ?? state.activeTemplate.textAreaWidth ?? 50, // Default 50mm or %? Let's assume mm if layout is fixed.
            textAreaHeight: textAreaHeight ?? state.activeTemplate.textAreaHeight ?? null,
            gap: gap ?? state.activeTemplate.gap ?? 0,
        }
    })),

    updateQrSettings: (newSettings) => set((state) => ({
        qrSettings: { ...state.qrSettings, ...newSettings }
    })),
}));

export default useLabelStore;
