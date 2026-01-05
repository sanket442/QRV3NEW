import React from 'react';
import useLabelStore from '../store/useLabelStore';

const PrintManager = () => {
    const { activeTemplate } = useLabelStore();

    // Dynamically generate the @page and grid CSS based on the selected template
    const printStyles = `
        @media print {
            @page {
                size: ${activeTemplate.width}mm ${activeTemplate.height}mm;
                margin: 0mm; 
            }

            #print-area {
                display: block;
                width: 100%;
            }

            .label-card {
                width: ${activeTemplate.width}mm;
                height: ${activeTemplate.height}mm;
                page-break-after: always;
                break-after: page;
                margin-bottom: ${activeTemplate.gap || 0}mm;
            }
        }
    `;

    return (
        <style>{printStyles}</style>
    );
};

export default PrintManager;
