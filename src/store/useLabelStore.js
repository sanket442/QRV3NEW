import { create } from 'zustand';
import { TEMPLATES } from '../templates/LabelTemplates';

const useLabelStore = create((set) => ({
    // Configuration
    activeTemplate: {
        ...TEMPLATES.FOLDED,
        width: parseFloat(localStorage.getItem('default_template_width')) || TEMPLATES.FOLDED.width,
        height: parseFloat(localStorage.getItem('default_template_height')) || TEMPLATES.FOLDED.height,
        gap: parseFloat(localStorage.getItem('default_template_gap')) || TEMPLATES.FOLDED.gap || 0,
        // Position Overrides (Defaults set to User Preference: 40, 4, 6, 8)
        qrX: parseFloat(localStorage.getItem('default_qr_x')) || 40,
        qrY: parseFloat(localStorage.getItem('default_qr_y')) || 4,
        textX: parseFloat(localStorage.getItem('default_text_x')) || 6,
        textY: parseFloat(localStorage.getItem('default_text_y')) || 8,
    },

    // QR Settings
    qrSettings: {
        format: 'QR',
        size: parseFloat(localStorage.getItem('default_qr_size_px')) || 70, // Default 70px
        ecc: localStorage.getItem('default_qr_ecc') || 'M', // Default to Medium (15%) or saved
        includeMargin: false,
    },

    // Actions
    setTemplate: (templateId) => set({
        activeTemplate: { ...(TEMPLATES[templateId] || TEMPLATES.FOLDED) }
    }),

    updateTemplateDimensions: (updates) => set((state) => ({
        activeTemplate: {
            ...state.activeTemplate,
            ...updates
        }
    })),

    updateQrSettings: (newSettings) => set((state) => ({
        qrSettings: { ...state.qrSettings, ...newSettings }
    })),
}));

export default useLabelStore;
