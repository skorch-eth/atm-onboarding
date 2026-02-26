const {
  Document, Packer, Paragraph, TextRun, AlignmentType,
  BorderStyle, Footer, TabStopType
} = require('docx');
const fs = require('fs');

const data = JSON.parse(process.argv[2]);
const outputPath = process.argv[3];

const m = data.merchant;
const b = data.bank;
const today = data.date || new Date().toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' });

const companyName = m.company_name;
const bankName = b.bank_name || '[Bank Name]';
const address = `${m.company_address}, ${m.company_city}, ${m.company_state} ${m.company_zip}`;
const fein = m.fein || '[EIN]';

function line(label, value) {
  return new Paragraph({
    spacing: { before: 0, after: 100 },
    children: [
      new TextRun({ text: label, font: 'Arial', size: 22, bold: true }),
      new TextRun({ text: `  ${value}`, font: 'Arial', size: 22 }),
    ]
  });
}

function blankLine(label) {
  return new Paragraph({
    spacing: { before: 0, after: 100 },
    children: [
      new TextRun({ text: label, font: 'Arial', size: 22, bold: true }),
      new TextRun({ text: '  _________________________________', font: 'Arial', size: 22 }),
    ]
  });
}

function spacer(after = 160) {
  return new Paragraph({ spacing: { before: 0, after }, children: [] });
}

const doc = new Document({
  styles: { default: { document: { run: { font: 'Arial', size: 22 } } } },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [

      new Paragraph({
        spacing: { before: 0, after: 200 },
        children: [new TextRun({ text: today, font: 'Arial', size: 22 })]
      }),

      new Paragraph({
        spacing: { before: 0, after: 80 },
        children: [new TextRun({ text: 'To Whom It May Concern', font: 'Arial', size: 22, bold: true })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 200 },
        children: [new TextRun({ text: bankName, font: 'Arial', size: 22 })]
      }),

      new Paragraph({
        spacing: { before: 0, after: 200 },
        children: [
          new TextRun({ text: 'RE: ', font: 'Arial', size: 22, bold: true }),
          new TextRun({ text: `Banking Relationship Letter — ${companyName}`, font: 'Arial', size: 22 }),
        ]
      }),

      new Paragraph({
        spacing: { before: 0, after: 160 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: '000000', space: 1 } },
        children: []
      }),

      new Paragraph({
        spacing: { before: 0, after: 120 },
        children: [new TextRun({ text: 'Bank Confirmation', font: 'Arial', size: 22, bold: true })]
      }),

      new Paragraph({
        spacing: { before: 0, after: 200 },
        children: [new TextRun({
          text: `The undersigned bank officer hereby confirms that ${companyName} has established a business banking relationship with ${bankName} and that the account information below is accurate.`,
          font: 'Arial', size: 22
        })]
      }),

      line('Bank Name:', bankName),
      line('Account Holder:', companyName),
      line('Principal Address:', address),
      line('Federal Employer Identification Number (FEIN):', fein),
      line('Account Type:', 'Business Checking'),
      blankLine('Routing Number:'),
      blankLine('Account Number:'),
      line('Account Status:', 'Active  /  In Good Standing'),

      spacer(200),

      new Paragraph({
        spacing: { before: 0, after: 80 },
        children: [new TextRun({ text: 'Bank Officer Signature:', font: 'Arial', size: 22, bold: true })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 160 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: '000000', space: 1 } },
        children: [new TextRun({ text: ' ', font: 'Arial', size: 44 })]
      }),

      new Paragraph({
        spacing: { before: 0, after: 100 },
        tabStops: [{ type: TabStopType.LEFT, position: 4680 }],
        children: [
          new TextRun({ text: 'Printed Name:  ___________________________', font: 'Arial', size: 22 }),
          new TextRun({ text: '\t', font: 'Arial', size: 22 }),
          new TextRun({ text: 'Title:  ___________________________', font: 'Arial', size: 22 }),
        ]
      }),
      new Paragraph({
        spacing: { before: 0, after: 200 },
        tabStops: [{ type: TabStopType.LEFT, position: 4680 }],
        children: [
          new TextRun({ text: 'Date:  ___________________________', font: 'Arial', size: 22 }),
          new TextRun({ text: '\t', font: 'Arial', size: 22 }),
          new TextRun({ text: 'Branch:  ___________________________', font: 'Arial', size: 22 }),
        ]
      }),

      new Paragraph({
        spacing: { before: 0, after: 80 },
        children: [new TextRun({ text: 'Bank Stamp / Seal:', font: 'Arial', size: 22, bold: true })]
      }),
      new Paragraph({
        border: {
          top: { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' },
          bottom: { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' },
          left: { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' },
          right: { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' },
        },
        children: [new TextRun({ text: ' ', font: 'Arial', size: 144 })]
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
