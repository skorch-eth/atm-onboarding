/**
 * EIN Application Answer Sheet Generator
 * Usage: node generate_ein_sheet.js '<json_string>' output.docx
 *
 * Generates a step-by-step copy-paste guide for completing the IRS
 * online EIN application at https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online
 * The entire application takes 5-10 minutes when following this sheet.
 */

const {
  Document, Packer, Paragraph, TextRun, AlignmentType,
  BorderStyle, Footer, TabStopType, ShadingType, Table,
  TableRow, TableCell, WidthType, VerticalAlign
} = require('docx');
const fs = require('fs');

const data = JSON.parse(process.argv[2]);
const outputPath = process.argv[3];

const m = data.merchant;
const today = data.date || new Date().toLocaleDateString('en-US', {
  month: 'long', day: 'numeric', year: 'numeric'
});

const companyName = m.company_name;
const signerName = m.entity_creator_name;
const signerTitle = m.title || 'Managing Member';
const address1 = m.company_address;
const city = m.company_city;
const state = m.company_state;
const zip = m.company_zip;
const phone = m.location_phone || m.company_phone || '';

// ── Helpers ────────────────────────────────────────────────────────────────

function spacer(after = 120) {
  return new Paragraph({ spacing: { before: 0, after }, children: [] });
}

function heading(text, color = '2C5282') {
  return new Paragraph({
    spacing: { before: 200, after: 80 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color, space: 2 } },
    children: [new TextRun({ text, font: 'Arial', size: 26, bold: true, color })]
  });
}

function intro(text) {
  return new Paragraph({
    spacing: { before: 0, after: 120 },
    children: [new TextRun({ text, font: 'Arial', size: 22, italics: true, color: '444444' })]
  });
}

function stepRow(stepNum, question, answer, note = '') {
  const cellBorder = { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' };
  const borders = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };
  const cellMargins = { top: 80, bottom: 80, left: 160, right: 160 };

  const answerCellChildren = [
    new Paragraph({
      spacing: { before: 0, after: note ? 60 : 0 },
      children: [new TextRun({ text: answer, font: 'Arial', size: 22, bold: true, color: '1A5276' })]
    })
  ];
  if (note) {
    answerCellChildren.push(new Paragraph({
      spacing: { before: 0, after: 0 },
      children: [new TextRun({ text: note, font: 'Arial', size: 18, italics: true, color: '666666' })]
    }));
  }

  return new TableRow({
    children: [
      new TableCell({
        borders,
        margins: cellMargins,
        width: { size: 640, type: WidthType.DXA },
        shading: { fill: 'EBF5FB', type: ShadingType.CLEAR },
        verticalAlign: VerticalAlign.TOP,
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: String(stepNum), font: 'Arial', size: 22, bold: true, color: '2C5282' })]
        })]
      }),
      new TableCell({
        borders,
        margins: cellMargins,
        width: { size: 3560, type: WidthType.DXA },
        verticalAlign: VerticalAlign.TOP,
        children: [new Paragraph({
          children: [new TextRun({ text: question, font: 'Arial', size: 22 })]
        })]
      }),
      new TableCell({
        borders,
        margins: cellMargins,
        width: { size: 5160, type: WidthType.DXA },
        shading: { fill: 'FDFEFE', type: ShadingType.CLEAR },
        verticalAlign: VerticalAlign.TOP,
        children: answerCellChildren
      }),
    ]
  });
}

function tableHeader() {
  const cellBorder = { style: BorderStyle.SINGLE, size: 4, color: '2C5282' };
  const borders = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };
  const cellMargins = { top: 80, bottom: 80, left: 160, right: 160 };
  return new TableRow({
    tableHeader: true,
    children: [
      new TableCell({
        borders, margins: cellMargins, width: { size: 640, type: WidthType.DXA },
        shading: { fill: '2C5282', type: ShadingType.CLEAR },
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '#', font: 'Arial', size: 20, bold: true, color: 'FFFFFF' })] })]
      }),
      new TableCell({
        borders, margins: cellMargins, width: { size: 3560, type: WidthType.DXA },
        shading: { fill: '2C5282', type: ShadingType.CLEAR },
        children: [new Paragraph({ children: [new TextRun({ text: 'IRS Question', font: 'Arial', size: 20, bold: true, color: 'FFFFFF' })] })]
      }),
      new TableCell({
        borders, margins: cellMargins, width: { size: 5160, type: WidthType.DXA },
        shading: { fill: '2C5282', type: ShadingType.CLEAR },
        children: [new Paragraph({ children: [new TextRun({ text: 'Your Answer (copy exactly)', font: 'Arial', size: 20, bold: true, color: 'FFFFFF' })] })]
      }),
    ]
  });
}

function makeTable(rows) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [640, 3560, 5160],
    rows: [tableHeader(), ...rows]
  });
}

// ── Parse phone for display ────────────────────────────────────────────────
const phoneClean = phone.replace(/\D/g, '');
const phoneFormatted = phoneClean.length === 10
  ? `${phoneClean.slice(0,3)}-${phoneClean.slice(3,6)}-${phoneClean.slice(6)}`
  : phone;

// ── Build document ─────────────────────────────────────────────────────────

const doc = new Document({
  styles: {
    default: { document: { run: { font: 'Arial', size: 22 } } }
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }
      }
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          children: [new TextRun({
            text: `EIN Application Answer Sheet  ·  ${companyName}  ·  Confidential — Contains Personal Information`,
            font: 'Arial', size: 16, color: '999999'
          })]
        })]
      })
    },
    children: [

      // ── Title block ────────────────────────────────────────────────────
      new Paragraph({
        spacing: { before: 0, after: 80 },
        children: [new TextRun({ text: 'EIN Application Answer Sheet', font: 'Arial', size: 36, bold: true, color: '2C5282' })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 80 },
        children: [new TextRun({ text: companyName, font: 'Arial', size: 26, bold: true })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 200 },
        children: [new TextRun({ text: `Prepared: ${today}`, font: 'Arial', size: 20, color: '666666' })]
      }),

      // ── Instructions box ───────────────────────────────────────────────
      new Paragraph({
        spacing: { before: 0, after: 0 },
        border: {
          top: { style: BorderStyle.SINGLE, size: 6, color: 'E67E22' },
          bottom: { style: BorderStyle.SINGLE, size: 6, color: 'E67E22' },
          left: { style: BorderStyle.SINGLE, size: 6, color: 'E67E22' },
          right: { style: BorderStyle.SINGLE, size: 6, color: 'E67E22' },
        },
        shading: { fill: 'FEF9E7', type: ShadingType.CLEAR },
        children: [new TextRun({ text: '', font: 'Arial', size: 4 })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 0 },
        shading: { fill: 'FEF9E7', type: ShadingType.CLEAR },
        border: {
          left: { style: BorderStyle.SINGLE, size: 6, color: 'E67E22' },
          right: { style: BorderStyle.SINGLE, size: 6, color: 'E67E22' },
        },
        children: [new TextRun({ text: '  ⚠  HOW TO USE THIS SHEET', font: 'Arial', size: 22, bold: true, color: 'E67E22' })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 0 },
        shading: { fill: 'FEF9E7', type: ShadingType.CLEAR },
        border: {
          left: { style: BorderStyle.SINGLE, size: 6, color: 'E67E22' },
          right: { style: BorderStyle.SINGLE, size: 6, color: 'E67E22' },
        },
        children: [new TextRun({ text: '  1. Open: https://irs.gov/ein  (search "IRS EIN online application")', font: 'Arial', size: 22 })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 0 },
        shading: { fill: 'FEF9E7', type: ShadingType.CLEAR },
        border: {
          left: { style: BorderStyle.SINGLE, size: 6, color: 'E67E22' },
          right: { style: BorderStyle.SINGLE, size: 6, color: 'E67E22' },
        },
        children: [new TextRun({ text: '  2. Click "Apply Online Now" — do NOT close the browser during the session (30-min timeout)', font: 'Arial', size: 22 })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 0 },
        shading: { fill: 'FEF9E7', type: ShadingType.CLEAR },
        border: {
          left: { style: BorderStyle.SINGLE, size: 6, color: 'E67E22' },
          right: { style: BorderStyle.SINGLE, size: 6, color: 'E67E22' },
        },
        children: [new TextRun({ text: '  3. Follow the steps below — answer each screen exactly as shown in blue', font: 'Arial', size: 22 })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 0 },
        shading: { fill: 'FEF9E7', type: ShadingType.CLEAR },
        border: {
          left: { style: BorderStyle.SINGLE, size: 6, color: 'E67E22' },
          right: { style: BorderStyle.SINGLE, size: 6, color: 'E67E22' },
        },
        children: [new TextRun({ text: '  4. At the end, download and save the EIN Confirmation Letter (CP 575) immediately', font: 'Arial', size: 22 })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 200 },
        border: {
          bottom: { style: BorderStyle.SINGLE, size: 6, color: 'E67E22' },
          left: { style: BorderStyle.SINGLE, size: 6, color: 'E67E22' },
          right: { style: BorderStyle.SINGLE, size: 6, color: 'E67E22' },
        },
        shading: { fill: 'FEF9E7', type: ShadingType.CLEAR },
        children: [new TextRun({ text: '  5. Note the EIN in the box at the bottom of this sheet', font: 'Arial', size: 22 })]
      }),

      // ── Section 1: Entity Type ─────────────────────────────────────────
      heading('SECTION 1 — Entity Type'),
      intro('The first screens ask what kind of entity is applying. Select exactly as shown.'),
      spacer(80),

      makeTable([
        stepRow(1, 'What type of legal structure is your business?', 'Limited Liability Company (LLC)'),
        stepRow(2, 'How many members does the LLC have?', '1',
          'Even if there are multiple — select 1 if a single member owns the LLC for tax purposes'),
        stepRow(3, 'Which state is the LLC organized in?', state),
      ]),

      spacer(160),

      // ── Section 2: Responsible Party ──────────────────────────────────
      heading('SECTION 2 — Responsible Party'),
      intro('The "responsible party" is the natural person who owns or controls the LLC. This person\'s SSN is required.'),
      spacer(80),

      makeTable([
        stepRow(4, 'First name', signerName.split(' ')[0] || signerName),
        stepRow(5, 'Last name', signerName.split(' ').slice(1).join(' ') || ''),
        stepRow(6, 'SSN or ITIN of responsible party', '***-**-****',
          '⚠ Fill in your actual SSN here — do not share this sheet after completing'),
        stepRow(7, 'Title / role', signerTitle),
      ]),

      spacer(160),

      // ── Section 3: Business Details ────────────────────────────────────
      heading('SECTION 3 — Business Information'),
      intro('These screens ask about the business itself.'),
      spacer(80),

      makeTable([
        stepRow(8, 'Legal name of business', companyName),
        stepRow(9, 'Trade name / DBA (if different)', m.dba_name !== m.company_name ? m.dba_name : 'Leave blank',
          m.dba_name !== m.company_name ? 'Enter DBA name if applicable' : 'Only fill if different from legal name'),
        stepRow(10, 'Business mailing address — Street', address1),
        stepRow(11, 'City', city),
        stepRow(12, 'State', state),
        stepRow(13, 'ZIP code', zip),
        stepRow(14, 'County', '',
          'Enter the county where the business is located (e.g., Miami-Dade)'),
        stepRow(15, 'Business phone number', phoneFormatted || '(enter business phone)'),
      ]),

      spacer(160),

      // ── Section 4: Business Type / Reason ─────────────────────────────
      heading('SECTION 4 — Why You\'re Applying'),
      intro('The IRS asks the reason for applying for an EIN.'),
      spacer(80),

      makeTable([
        stepRow(16, 'Why are you applying for an EIN?', 'Started a new business'),
        stepRow(17, 'Date business started or was acquired', today,
          'Use today\'s date or the LLC formation date if already filed'),
        stepRow(18, 'Closing month of your accounting year', 'December'),
        stepRow(19, 'Highest number of employees expected in 12 months', '0',
          'If you don\'t plan to have W-2 employees, enter 0'),
        stepRow(20, 'Does the business have, or expect to have, employees?', 'No',
          'Select No if no W-2 payroll — you can always get a payroll EIN later'),
        stepRow(21, 'Principal activity of your business', 'Finance and Insurance',
          'ATM operation falls under financial services'),
        stepRow(22, 'Specific product or service', 'ATM operation and management'),
      ]),

      spacer(200),

      // ── EIN record box ─────────────────────────────────────────────────
      heading('RECORD YOUR EIN HERE', 'C0392B'),
      intro('After submitting, the IRS shows your EIN immediately. Write it here before closing the window.'),
      spacer(80),

      new Paragraph({
        spacing: { before: 0, after: 0 },
        border: {
          top: { style: BorderStyle.SINGLE, size: 8, color: 'C0392B' },
          bottom: { style: BorderStyle.SINGLE, size: 8, color: 'C0392B' },
          left: { style: BorderStyle.SINGLE, size: 8, color: 'C0392B' },
          right: { style: BorderStyle.SINGLE, size: 8, color: 'C0392B' },
        },
        shading: { fill: 'FDEDEC', type: ShadingType.CLEAR },
        children: [new TextRun({ text: ' ', font: 'Arial', size: 8 })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        border: {
          left: { style: BorderStyle.SINGLE, size: 8, color: 'C0392B' },
          right: { style: BorderStyle.SINGLE, size: 8, color: 'C0392B' },
        },
        shading: { fill: 'FDEDEC', type: ShadingType.CLEAR },
        children: [
          new TextRun({ text: `EIN for ${companyName}:   `, font: 'Arial', size: 24, bold: true }),
          new TextRun({ text: '__ __ - __ __ __ __ __ __ __', font: 'Courier New', size: 28, bold: true, color: 'C0392B' }),
        ]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        border: {
          left: { style: BorderStyle.SINGLE, size: 8, color: 'C0392B' },
          right: { style: BorderStyle.SINGLE, size: 8, color: 'C0392B' },
        },
        shading: { fill: 'FDEDEC', type: ShadingType.CLEAR },
        children: [new TextRun({ text: 'Download the CP 575 confirmation letter and send a copy to your ISO', font: 'Arial', size: 20, italics: true, color: '666666' })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 160 },
        border: {
          bottom: { style: BorderStyle.SINGLE, size: 8, color: 'C0392B' },
          left: { style: BorderStyle.SINGLE, size: 8, color: 'C0392B' },
          right: { style: BorderStyle.SINGLE, size: 8, color: 'C0392B' },
        },
        shading: { fill: 'FDEDEC', type: ShadingType.CLEAR },
        children: [new TextRun({ text: ' ', font: 'Arial', size: 8 })]
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
