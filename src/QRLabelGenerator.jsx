import React, { useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { FileSpreadsheet, Type, Printer, Settings, ArrowRight, FileText, QrCode, Layers, FoldHorizontal, LayoutTemplate } from 'lucide-react';
import useLabelStore from './store/useLabelStore';
import { TEMPLATES } from './templates/LabelTemplates';
import PrintManager from './components/PrintManager';

const QRLabelGenerator = () => {
    // Global Store
    const { activeTemplate, setTemplate, qrSettings, updateQrSettings } = useLabelStore();

    const [activeTab, setActiveTab] = useState('sheet');
    const [labels, setLabels] = useState([]);

    // Manual Input State
    const [manualQrText, setManualQrText] = useState('');
    const [manualLabelText, setManualLabelText] = useState('');

    // Sheet Input State
    const [sheetUrl, setSheetUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [sheetData, setSheetData] = useState([]);
    const [headers, setHeaders] = useState([]);
    const [columnMapping, setColumnMapping] = useState({ qr: '', label: '' });

    // Row Range Selectors
    const [rangeStart, setRangeStart] = useState(2);
    const [rangeEnd, setRangeEnd] = useState(100);

    const [step, setStep] = useState(1);
    const [showSettings, setShowSettings] = useState(false);

    // Parse Google Sheet ID
    const getSheetId = (url) => {
        const regExp = /\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/;
        const matches = url.match(regExp);
        return matches ? matches[1] : null;
    };

    // Robust CSV Parser
    const parseCSV = (csvText) => {
        const rows = [];
        let currentRow = [];
        let currentCell = '';
        let insideQuote = false;

        for (let i = 0; i < csvText.length; i++) {
            const char = csvText[i];
            const nextChar = csvText[i + 1];

            if (char === '"') {
                if (insideQuote && nextChar === '"') {
                    currentCell += '"';
                    i++;
                } else {
                    insideQuote = !insideQuote;
                }
            } else if (char === ',' && !insideQuote) {
                currentRow.push(currentCell.trim());
                currentCell = '';
            } else if ((char === '\r' || char === '\n') && !insideQuote) {
                if (char === '\r' && nextChar === '\n') i++;

                if (currentCell || currentRow.length > 0) {
                    currentRow.push(currentCell.trim());
                    rows.push(currentRow);
                }
                currentCell = '';
                currentRow = [];
            } else {
                currentCell += char;
            }
        }

        if (currentCell || currentRow.length > 0) {
            currentRow.push(currentCell.trim());
            rows.push(currentRow);
        }

        return rows;
    };


    // 1. Fetch Sheet Data
    const fetchSheetData = async () => {
        const sheetId = getSheetId(sheetUrl);
        if (!sheetId) {
            alert('Invalid Google Sheet URL');
            return;
        }

        setLoading(true);
        try {
            const csvUrl = `https://docs.google.com/spreadsheets/d/${sheetId}/export?format=csv`;
            const response = await fetch(csvUrl);
            if (!response.ok) throw new Error('Failed to fetch. Ensure Sheet is "Published to Web"');

            const text = await response.text();
            const rows = parseCSV(text);

            if (rows.length > 0) {
                setHeaders(rows[0]);
                setSheetData(rows.slice(1));
                setRangeEnd(rows.length);
                setStep(2);
            }
        } catch (error) {
            console.error(error);
            alert('Error fetching sheet. Make sure File > Share > Publish to web is enabled.');
        } finally {
            setLoading(false);
        }
    };

    // 2. Generate Labels
    const generateFromSheet = () => {
        if (!columnMapping.qr || !columnMapping.label) {
            alert('Please select both columns!');
            return;
        }

        const qrIndex = headers.indexOf(columnMapping.qr);
        const labelIndex = headers.indexOf(columnMapping.label);

        const startIdx = Math.max(0, rangeStart - 2);
        const endIdx = Math.min(sheetData.length, rangeEnd - 1);

        const validData = sheetData.slice(startIdx, endIdx);

        const newLabels = validData.map((row, idx) => ({
            qrData: row[qrIndex] || 'N/A',
            labelText: row[labelIndex] || 'N/A',
            id: `sheet-${Date.now()}-${idx}`
        })).filter(l => l.qrData !== 'N/A' && l.qrData !== '');

        setLabels(prev => [...prev, ...newLabels]);
        setStep(1);
        setSheetUrl('');
        setSheetData([]);
    };

    const handleManualAdd = () => {
        if (manualQrText.trim()) {
            setLabels([...labels, {
                qrData: manualQrText,
                labelText: manualLabelText || manualQrText,
                id: Date.now()
            }]);
            setManualQrText('');
            setManualLabelText('');
        }
    };

    const clearLabels = () => setLabels([]);

    const handlePrint = () => {
        window.print();
    }

    // Helper to calculate Preview scale (approx)
    // 1mm ~ 3.78px.
    const PREVIEW_SCALE = 3;

    // Dynamic Style Helper
    const getContainerStyle = (isPrint = false) => {
        const scale = isPrint ? 1 : PREVIEW_SCALE;
        // Logic: If user sets explicit text area W/H, we use it. 
        // Gap is applied as margin in print grid.
        return {
            width: `${activeTemplate.width * scale}px`,
            height: `${activeTemplate.height * scale}px`,
        };
    };

    return (
        <div className="min-h-screen bg-slate-950 flex flex-col font-sans text-slate-100">
            {/* Inject Dynamic Print Styles including GAP */}
            {/* We will need to pass Gap to PrintManager or inject custom style here for grid gap */}
            <PrintManager template={activeTemplate} />

            {/* Inject Gap Style Override for Print */}
            <style>
                {`
                    @media print {
                        .print-grid {
                            gap: ${activeTemplate.gap || 0}mm !important;
                        }
                    }
                `}
            </style>

            {/* Navbar */}
            <nav className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex justify-between items-center sticky top-0 z-10 shadow-md shadow-black/20 no-print">
                <div className="flex items-center gap-3">
                    <div className="bg-indigo-600 p-2 rounded-lg">
                        <QrCode className="text-white w-6 h-6" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-white tracking-tight">QR Label Pro <span className="text-indigo-400 text-sm font-normal">v2.2</span></h1>
                        <p className="text-xs text-slate-400 font-medium">{activeTemplate.name} ({activeTemplate.width}x{activeTemplate.height}mm)</p>
                    </div>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => setShowSettings(!showSettings)}
                        className={`text-slate-400 hover:text-white transition-colors p-2 rounded-lg ${showSettings ? 'bg-slate-800 text-white' : ''}`}
                    >
                        <Settings size={20} />
                    </button>
                </div>
            </nav>

            <main className="flex-1 p-4 md:p-8 max-w-[1600px] mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-8">

                {/* Left Panel: Input Controls (Hidden in Print) */}
                <div className="lg:col-span-4 space-y-6 no-print">

                    {/* SETTINGS PANEL (Conditional) */}
                    {showSettings && (
                        <div className="bg-slate-900 rounded-2xl shadow-xl border border-slate-800 p-6 animate-in fade-in slide-in-from-top-2">
                            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">Advance Layout Config</h3>

                            <div className="space-y-6">
                                <div>
                                    <label className="block text-xs font-semibold text-slate-500 mb-2">Base Template</label>
                                    <div className="grid grid-cols-2 gap-2">
                                        {Object.values(TEMPLATES).map(t => (
                                            <button
                                                key={t.id}
                                                onClick={() => setTemplate(t.id)}
                                                className={`p-3 rounded-lg border text-left transition-all flex flex-col items-center gap-2 ${activeTemplate.id === t.id ? 'border-indigo-500 bg-indigo-500/10 text-indigo-300' : 'border-slate-700 bg-slate-800 hover:bg-slate-750'}`}
                                            >
                                                {t.id === 'FOLDED' ? <FoldHorizontal size={20} /> : <LayoutTemplate size={20} />}
                                                <span className="text-xs font-medium">{t.name}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* 1. Tag Size & Gap */}
                                <div className="p-3 bg-slate-950/50 rounded-lg border border-slate-800">
                                    <label className="block text-xs font-bold text-indigo-400 mb-3 uppercase tracking-wider">Tag Dimensions</label>
                                    <div className="grid grid-cols-3 gap-3">
                                        <div>
                                            <label className="text-[10px] text-slate-400 mb-1 block">Width (mm)</label>
                                            <input
                                                type="number"
                                                value={activeTemplate.width}
                                                onChange={(e) => useLabelStore.getState().updateTemplateDimensions(parseFloat(e.target.value), undefined)}
                                                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-center focus:border-indigo-500 outline-none"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-[10px] text-slate-400 mb-1 block">Height (mm)</label>
                                            <input
                                                type="number"
                                                value={activeTemplate.height}
                                                onChange={(e) => useLabelStore.getState().updateTemplateDimensions(undefined, parseFloat(e.target.value))}
                                                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-center focus:border-indigo-500 outline-none"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-[10px] text-slate-400 mb-1 block">Gap (mm)</label>
                                            <input
                                                type="number"
                                                value={activeTemplate.gap || 0}
                                                onChange={(e) => useLabelStore.getState().updateTemplateDimensions(undefined, undefined, undefined, undefined, undefined, undefined, parseFloat(e.target.value))}
                                                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-center focus:border-indigo-500 outline-none"
                                                placeholder="0"
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* 2. Text Area Customization */}
                                <div className="p-3 bg-slate-950/50 rounded-lg border border-slate-800">
                                    <label className="block text-xs font-bold text-indigo-400 mb-3 uppercase tracking-wider">Component Sizes</label>
                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="text-[10px] text-slate-400 mb-1 block">QR Size (px)</label>
                                            <input
                                                type="number"
                                                value={qrSettings.size}
                                                onChange={(e) => updateQrSettings({ size: parseInt(e.target.value) })}
                                                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-center focus:border-indigo-500 outline-none"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-[10px] text-slate-400 mb-1 block">ECC Level</label>
                                            <select
                                                value={qrSettings.ecc}
                                                onChange={(e) => updateQrSettings({ ecc: e.target.value })}
                                                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm focus:border-indigo-500 outline-none"
                                            >
                                                <option value="L">L (7%)</option>
                                                <option value="M">M (15%)</option>
                                                <option value="Q">Q (25%)</option>
                                                <option value="H">H (30%)</option>
                                            </select>
                                        </div>
                                    </div>

                                    <div className="mt-3 grid grid-cols-2 gap-3 pt-3 border-t border-slate-800/50">
                                        <div className="col-span-2 text-[10px] font-semibold text-slate-500 uppercase">Text Area Override (Optional)</div>
                                        <div>
                                            <label className="text-[10px] text-slate-400 mb-1 block">Width (mm)</label>
                                            <input
                                                type="number"
                                                value={activeTemplate.textAreaWidth || ''}
                                                onChange={(e) => useLabelStore.getState().updateTemplateDimensions(undefined, undefined, undefined, undefined, parseFloat(e.target.value), undefined)}
                                                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-center focus:border-indigo-500 outline-none"
                                                placeholder="Auto"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-[10px] text-slate-400 mb-1 block">Height (mm)</label>
                                            <input
                                                type="number"
                                                value={activeTemplate.textAreaHeight || ''}
                                                onChange={(e) => useLabelStore.getState().updateTemplateDimensions(undefined, undefined, undefined, undefined, undefined, parseFloat(e.target.value))}
                                                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-center focus:border-indigo-500 outline-none"
                                                placeholder="Auto"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="bg-slate-900 rounded-2xl shadow-xl border border-slate-800 overflow-hidden">
                        {/* Tabs */}
                        <div className="flex border-b border-slate-800">
                            <button
                                onClick={() => setActiveTab('sheet')}
                                className={`flex-1 py-4 text-sm font-semibold flex justify-center items-center gap-2 transition-colors ${activeTab === 'sheet' ? 'bg-slate-800/50 text-indigo-400 border-b-2 border-indigo-400' : 'text-slate-500 hover:bg-slate-800 hover:text-white'}`}
                            >
                                <FileSpreadsheet size={18} /> Google Sheet
                            </button>
                            <button
                                onClick={() => setActiveTab('manual')}
                                className={`flex-1 py-4 text-sm font-semibold flex justify-center items-center gap-2 transition-colors ${activeTab === 'manual' ? 'bg-slate-800/50 text-indigo-400 border-b-2 border-indigo-400' : 'text-slate-500 hover:bg-slate-800 hover:text-white'}`}
                            >
                                <Type size={18} /> Manual Input
                            </button>
                        </div>

                        <div className="p-6">
                            {activeTab === 'sheet' && (
                                <div className="space-y-4">

                                    {step === 1 && (
                                        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                                            <div>
                                                <label className="block text-sm font-medium text-slate-300 mb-1">Google Sheet URL</label>
                                                <input
                                                    type="text"
                                                    value={sheetUrl}
                                                    onChange={(e) => setSheetUrl(e.target.value)}
                                                    placeholder="https://docs.google.com/spreadsheets/d/..."
                                                    className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700 text-white placeholder-slate-600 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all text-sm"
                                                />
                                            </div>
                                            <button
                                                onClick={fetchSheetData}
                                                disabled={loading || !sheetUrl}
                                                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2 shadow-lg shadow-indigo-900/20"
                                            >
                                                {loading ? <span className="animate-pulse">Loading...</span> : <>Load Columns <ArrowRight size={18} /></>}
                                            </button>
                                        </div>
                                    )}

                                    {step === 2 && (
                                        <div className="space-y-5 animate-in fade-in slide-in-from-right-4 duration-300">
                                            <div className="bg-green-900/20 text-green-400 border border-green-900/50 p-3 rounded-lg text-sm flex items-center gap-2">
                                                <FileText size={16} /> Data Loaded! {headers.length} Columns found.
                                            </div>

                                            {/* Column Mapping */}
                                            <div className="grid grid-cols-1 gap-4">
                                                <div>
                                                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">1. Select QR Data Column</label>
                                                    <select
                                                        value={columnMapping.qr}
                                                        onChange={(e) => setColumnMapping({ ...columnMapping, qr: e.target.value })}
                                                        className="w-full p-3 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white outline-none focus:ring-2 focus:ring-indigo-500"
                                                    >
                                                        <option value="">-- Choose Column --</option>
                                                        {headers.map(h => <option key={h} value={h}>{h}</option>)}
                                                    </select>
                                                </div>

                                                <div>
                                                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">2. (Optional) Display Label Column</label>
                                                    <select
                                                        value={columnMapping.label}
                                                        onChange={(e) => setColumnMapping({ ...columnMapping, label: e.target.value })}
                                                        className="w-full p-3 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white outline-none focus:ring-2 focus:ring-indigo-500"
                                                    >
                                                        <option value="">-- Choose Column --</option>
                                                        {headers.map(h => <option key={h} value={h}>{h}</option>)}
                                                    </select>
                                                </div>
                                            </div>

                                            {/* Row Range Selection */}
                                            <div className="pt-2 border-t border-slate-800">
                                                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-2">
                                                    <Layers size={14} /> Row Range Selection
                                                </label>
                                                <div className="flex gap-4">
                                                    <div className="flex-1">
                                                        <span className="text-xs text-slate-500 block mb-1">Start Row</span>
                                                        <input
                                                            type="number"
                                                            value={rangeStart}
                                                            onChange={(e) => setRangeStart(parseInt(e.target.value) || 1)}
                                                            className="w-full p-2 bg-slate-950 border border-slate-700 rounded text-white text-center"
                                                        />
                                                    </div>
                                                    <div className="flex-1">
                                                        <span className="text-xs text-slate-500 block mb-1">End Row</span>
                                                        <input
                                                            type="number"
                                                            value={rangeEnd}
                                                            onChange={(e) => setRangeEnd(parseInt(e.target.value) || 1)}
                                                            className="w-full p-2 bg-slate-950 border border-slate-700 rounded text-white text-center"
                                                        />
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex gap-2 pt-2">
                                                <button
                                                    onClick={() => setStep(1)}
                                                    className="flex-1 px-4 py-2 text-slate-400 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-700 font-medium hover:text-white"
                                                >
                                                    Back
                                                </button>
                                                <button
                                                    onClick={generateFromSheet}
                                                    className="flex-[2] bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-500 shadow-md shadow-indigo-900/20"
                                                >
                                                    Generate Labels
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                </div>
                            )}

                            {activeTab === 'manual' && (
                                <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-1">QR Code Content</label>
                                        <input
                                            type="text"
                                            value={manualQrText}
                                            onChange={(e) => setManualQrText(e.target.value)}
                                            placeholder="e.g. SKU-12345"
                                            className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700 text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all text-sm font-mono"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-1">Visible Label Text</label>
                                        <textarea
                                            rows={2}
                                            value={manualLabelText}
                                            onChange={(e) => setManualLabelText(e.target.value)}
                                            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleManualAdd()}
                                            placeholder="e.g. Blue Widget (Small)"
                                            className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700 text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all text-sm"
                                        />
                                        <p className="text-[10px] text-slate-500 mt-1">*Text depends on Template config</p>
                                    </div>
                                    <button
                                        onClick={handleManualAdd}
                                        disabled={!manualQrText}
                                        className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 rounded-xl transition-all disabled:opacity-50 shadow-lg shadow-blue-900/20"
                                    >
                                        Add Label
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Panel: Preview and Print */}
                <div className="lg:col-span-8 space-y-6">

                    <div className="flex items-center justify-between no-print">
                        <h2 className="text-xl font-bold text-white flex items-center gap-2">
                            Labels Preview <span className="bg-indigo-900/50 text-indigo-300 px-3 py-1 rounded-full text-xs border border-indigo-500/30">{labels.length}</span>
                        </h2>
                        {labels.length > 0 && (
                            <button onClick={clearLabels} className="text-red-400 hover:text-red-300 font-medium text-sm transition-colors border-b border-transparent hover:border-red-400">
                                Clear Queue
                            </button>
                        )}
                    </div>

                    {/* Print Visualization / Queue */}
                    <div id="print-area" className="bg-transparent">

                        {/* 
                            SCREEN PREVIEW LIST 
                            Visualizes the label roughly as it appears, but scaled up for visibility if needed.
                        */}
                        <div className="no-print bg-slate-900/50 rounded-2xl border border-slate-800 p-6 min-h-[400px] max-h-[600px] overflow-auto flex flex-col items-center gap-4">
                            {labels.length === 0 ? (
                                <div className="text-slate-600 font-medium">No labels ready.</div>
                            ) : (
                                labels.map((label) => (
                                    <div
                                        key={label.id}
                                        className="bg-white text-black rounded shadow-md opacity-90 overflow-hidden shrink-0 relative transition-transform hover:scale-[1.02]"
                                        style={getContainerStyle(false)}
                                    >
                                        {/* FOLDED TAG LAYOUT */}
                                        {activeTemplate.layout === 'folded' ? (
                                            <div className="flex h-full">
                                                {/* Left: Text */}
                                                <div
                                                    className="h-full flex flex-col justify-center px-2 py-1 overflow-hidden"
                                                    style={{
                                                        width: activeTemplate.textAreaWidth ? `${activeTemplate.textAreaWidth}mm` : '50%'
                                                    }}
                                                >
                                                    <div className="text-[10px] font-bold leading-tight break-words">{label.labelText}</div>
                                                </div>

                                                {/* Fold Line */}
                                                <div className="h-full border-l border-dashed border-gray-400 flex items-center justify-center relative">
                                                </div>

                                                {/* Right: QR */}
                                                <div className="flex-1 flex items-center justify-center p-1">
                                                    <QRCodeSVG
                                                        value={label.qrData}
                                                        size={qrSettings.size}
                                                        level={qrSettings.ecc}
                                                        includeMargin={false}
                                                    />
                                                </div>
                                            </div>
                                        ) : (
                                            // STANDARD LAYOUT
                                            <div className="flex items-center justify-between px-4 h-full">
                                                <span
                                                    className="text-[10px] sm:text-xs break-words font-semibold"
                                                    style={{
                                                        width: activeTemplate.textAreaWidth ? `${activeTemplate.textAreaWidth}mm` : '50%'
                                                    }}
                                                >{label.labelText}</span>
                                                <QRCodeSVG
                                                    value={label.qrData}
                                                    size={qrSettings.size}
                                                    level={qrSettings.ecc}
                                                />
                                            </div>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>

                        {/* 
                            ACTUAL PRINT STRUCTURE 
                        */}
                        <div className="print-grid hidden">
                            {labels.map((label) => (
                                <div key={label.id} className="label-card">

                                    {/* FOLDED PRINT LAYOUT */}
                                    {activeTemplate.layout === 'folded' ? (
                                        <div className="w-full h-full flex">
                                            {/* Left: Text - Rotated 180 degrees */}
                                            <div
                                                className="h-full flex flex-col justify-center items-start pl-2 overflow-hidden rotate-180"
                                                style={{
                                                    width: activeTemplate.textAreaWidth ? `${activeTemplate.textAreaWidth}mm` : '50%'
                                                }}
                                            >
                                                <div className="text-[8pt] font-sans font-bold leading-tight">{label.labelText}</div>
                                            </div>

                                            {/* Right: QR */}
                                            <div className="flex-1 h-full flex items-center justify-center">
                                                <QRCodeSVG
                                                    value={label.qrData}
                                                    size={qrSettings.size}
                                                    level={qrSettings.ecc}
                                                    includeMargin={false}
                                                />
                                            </div>
                                        </div>
                                    ) : (
                                        // STANDARD PRINT LAYOUT
                                        <div className="printable-area w-full h-full flex items-center justify-center gap-2">
                                            {/* Legacy Standard: usually just QR, but we added text support above if needed. */}
                                            <QRCodeSVG
                                                value={label.qrData}
                                                size={qrSettings.size}
                                                level={qrSettings.ecc}
                                                includeMargin={false}
                                            />
                                        </div>
                                    )}

                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Floating Action Bar */}
                    <div className="fixed bottom-6 right-6 md:right-10 flex gap-4 no-print">
                        <button
                            onClick={handlePrint}
                            className="bg-indigo-600 text-white px-8 py-4 rounded-full shadow-2xl hover:bg-indigo-500 hover:scale-105 active:scale-95 transition-all font-bold flex items-center gap-3 shadow-indigo-900/50 ring-4 ring-slate-950"
                        >
                            <Printer /> Print Labels
                        </button>
                    </div>

                </div>

            </main>
        </div>
    );
};

export default QRLabelGenerator;
