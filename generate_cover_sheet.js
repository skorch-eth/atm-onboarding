const {
  Document, Packer, Paragraph, TextRun, AlignmentType,
  BorderStyle, Table, TableRow, TableCell, WidthType,
  ShadingType, VerticalAlign, TabStopType
} = require('docx');
const fs = require('fs');

const data = JSON.parse(process.argv[2]);
const outputPath = process.argv[3];

const m = data.merchant;
const b = data.bank;
const today = data.date || new Date().toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' });
const companyName = m.company_name;
const dba = m.dba_name && m.dba_name !== m.company_name ? m.dba_name : null;
const ownerName = m.entity_creator_name;
const state = m.company_state;
const address = `${m.company_address}, ${m.company_city}, ${m.company_state} ${m.company_zip}`;
const phone = m.location_phone || '';
const email = m.email || '';
const fein = m.fein || '';

// ── Helpers ────────────────────────────────────────────────────────────────

const BLUE = '1A3C5E';
const LIGHT_BLUE = 'EAF1F8';
const MID_BLUE = '2C5F8A';
const GRAY = '666666';
const RULE_COLOR = 'BBCFE0';

function spacer(after = 80) {
  return new Paragraph({ spacing: { before: 0, after }, children: [] });
}

const cellBorder = { style: BorderStyle.SINGLE, size: 4, color: RULE_COLOR };
const borders = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };
const noBorder = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };
const cellPad = { top: 60, bottom: 60, left: 140, right: 140 };

function infoRow(label, value) {
  return new TableRow({
    children: [
      new TableCell({
        borders,
        margins: cellPad,
        width: { size: 1600, type: WidthType.DXA },
        shading: { fill: LIGHT_BLUE, type: ShadingType.CLEAR },
        children: [new Paragraph({
          children: [new TextRun({ text: label, font: 'Arial', size: 15, bold: true, color: BLUE })]
        })]
      }),
      new TableCell({
        borders,
        margins: cellPad,
        width: { size: 6960, type: WidthType.DXA },
        children: [new Paragraph({
          children: [new TextRun({ text: value || '—', font: 'Arial', size: 15, color: value ? '000000' : GRAY })]
        })]
      }),
    ]
  });
}

function stepRow(num, title, items, statusLabel = '□ Pending') {
  const statusColor = statusLabel.includes('✓') ? '1A6B3A' : statusLabel.includes('●') ? '8B5E00' : GRAY;
  return new TableRow({
    children: [
      // Step number
      new TableCell({
        borders,
        margins: { top: 120, bottom: 120, left: 140, right: 140 },
        width: { size: 600, type: WidthType.DXA },
        shading: { fill: BLUE, type: ShadingType.CLEAR },
        verticalAlign: VerticalAlign.TOP,
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: String(num), font: 'Arial', size: 26, bold: true, color: 'FFFFFF' })]
        })]
      }),
      // Title + items
      new TableCell({
        borders,
        margins: { top: 100, bottom: 100, left: 160, right: 160 },
        width: { size: 6860, type: WidthType.DXA },
        verticalAlign: VerticalAlign.TOP,
        children: [
          new Paragraph({
            spacing: { before: 0, after: 60 },
            children: [new TextRun({ text: title, font: 'Arial', size: 16, bold: true, color: BLUE })]
          }),
          ...items.map(item => new Paragraph({
            spacing: { before: 0, after: 20 },
            children: [new TextRun({ text: `  ${item}`, font: 'Arial', size: 15, color: '333333' })]
          }))
        ]
      }),
      // Status + date
      new TableCell({
        borders,
        margins: { top: 100, bottom: 100, left: 140, right: 140 },
        width: { size: 1500, type: WidthType.DXA },
        shading: { fill: 'F7FAFD', type: ShadingType.CLEAR },
        verticalAlign: VerticalAlign.TOP,
        children: [
          new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { before: 0, after: 80 },
            children: [new TextRun({ text: statusLabel, font: 'Arial', size: 15, bold: true, color: statusColor })]
          }),
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: 'Date: __________', font: 'Arial', size: 15, color: GRAY })]
          }),
        ]
      }),
    ]
  });
}

function docCheckRow(docName, included = true) {
  return new TableRow({
    children: [
      new TableCell({
        borders,
        margins: cellPad,
        width: { size: 600, type: WidthType.DXA },
        shading: { fill: included ? 'EAF7EF' : 'FEF9E7', type: ShadingType.CLEAR },
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: included ? '☑' : '☐', font: 'Arial', size: 16, color: included ? '1A6B3A' : '8B5E00' })]
        })]
      }),
      new TableCell({
        borders,
        margins: cellPad,
        width: { size: 8760, type: WidthType.DXA },
        children: [new Paragraph({
          children: [new TextRun({ text: docName, font: 'Arial', size: 16, color: '222222' })]
        })]
      }),
    ]
  });
}

// ── Document ───────────────────────────────────────────────────────────────

const doc = new Document({
  styles: { default: { document: { run: { font: 'Arial', size: 16 } } } },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 720, right: 900, bottom: 720, left: 900 }
      }
    },
    children: [

      // ── Header bar (simulated with top border paragraph) ───────────────
      new Paragraph({
        spacing: { before: 0, after: 0 },
        border: { top: { style: BorderStyle.SINGLE, size: 32, color: BLUE, space: 0 } },
        shading: { fill: BLUE, type: ShadingType.CLEAR },
        children: [new TextRun({ text: ' ', font: 'Arial', size: 4 })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 0 },
        shading: { fill: BLUE, type: ShadingType.CLEAR },
        children: [new TextRun({ text: '  ATM MERCHANT ONBOARDING', font: 'Arial', size: 16, bold: true, color: 'FFFFFF' })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 0 },
        shading: { fill: BLUE, type: ShadingType.CLEAR },
        children: [new TextRun({ text: '  PACKET COVER SHEET', font: 'Arial', size: 16, bold: true, color: 'FFFFFF' })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 200 },
        shading: { fill: BLUE, type: ShadingType.CLEAR },
        border: { bottom: { style: BorderStyle.SINGLE, size: 32, color: BLUE, space: 0 } },
        children: [new TextRun({ text: ' ', font: 'Arial', size: 4 })]
      }),

      // ── Merchant Info ──────────────────────────────────────────────────
      new Paragraph({
        spacing: { before: 0, after: 100 },
        children: [new TextRun({ text: 'MERCHANT INFORMATION', font: 'Arial', size: 16, bold: true, color: MID_BLUE })]
      }),

      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2400, 6960],
        rows: [
          infoRow('Legal Entity Name', companyName),

          infoRow('Owner / Managing Member', ownerName),
          infoRow('State of Formation', state),
          infoRow('Principal Address', address),
          infoRow('Phone', phone),
          infoRow('Email', email),
          infoRow('FEIN', fein || 'Pending — see EIN Answer Sheet'),
          infoRow('Bank', b.bank_name || ''),
          infoRow('Date Prepared', today),
        ]
      }),

      spacer(80),

      // ── 4-Step Status Tracker ──────────────────────────────────────────
      new Paragraph({
        spacing: { before: 0, after: 100 },
        children: [new TextRun({ text: 'ONBOARDING STATUS', font: 'Arial', size: 16, bold: true, color: MID_BLUE })]
      }),

      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [600, 6860, 1900],
        rows: [
          stepRow(1, 'File for LLC', [
            '□ Articles of Organization submitted',
            '□ State filing fee paid',
            '□ Approval documents received',
            '□ Operating Agreement drafted',
          ]),
          stepRow(2, 'Obtain EIN', [
            '□ IRS online application completed (irs.gov/ein)',
            '□ CP 575 confirmation letter downloaded',
            '□ EIN recorded: ____________________________',
          ]),
          stepRow(3, 'Open Bank Account', [
            '□ Business checking account opened',
            '□ Routing number obtained',
            '□ Account number obtained',
            '□ Banking Relationship Letter signed & stamped',
          ]),
          stepRow(4, 'Submit Processing Forms', [
            '□ Exhibit 2 — ATM Operator Agreement signed',
            '□ Exhibit 3 — ACH Authorization Form signed',
            '□ W-9 signed',
            '□ Full packet submitted to ISO / PAI',
          ]),
        ]
      }),

      // ── Documents in Packet ────────────────────────────────────────────
      new Paragraph({
        spacing: { before: 0, after: 100 },
        children: [new TextRun({ text: 'DOCUMENTS IN THIS PACKET', font: 'Arial', size: 16, bold: true, color: MID_BLUE })]
      }),

      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [600, 8760],
        rows: [
          docCheckRow('Exhibit 2 — ATM Operator / Source of Funds Provider Agreement'),
          docCheckRow('Exhibit 3 — ACH Authorization Form'),
          docCheckRow('W-9 — Taxpayer Identification'),
          docCheckRow('Banking Relationship Letter'),
          docCheckRow('EIN Application Answer Sheet'),
        ]
      }),

    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outputPath, buffer);
  console.log('OK: ' + outputPath);
}).catch(err => {
  console.error('ERROR: ' + err.message);
  process.exit(1);
});
