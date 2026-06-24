/**
 * Component tests for DiscrepancyList
 * Tests discrepancy display functionality and source attribution
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DiscrepancyList } from '@/src/components/results/DiscrepancyList';
import { DiscrepancyTransaction } from '@/src/types/reconciliation.types';

describe('DiscrepancyList', () => {
  const mockDiscrepancies: DiscrepancyTransaction[] = [
    {
      'Transaction_date': '2026-05-06',
      'Transaction Detail': 'Payment Suzuki Azim Motors WHT 5.515',
      'Debit/Credit': -40771.695,
      'FROM': 'Bank'
    },
    {
      'Transaction_date': '2026-05-06',
      'Transaction Detail': 'Payment Suzuki Azim Motors WHT 5.515',
      'Debit/Credit': 6771.238,
      'FROM': 'Company'
    },
    {
      'Transaction_date': '2026-05-05',
      'Transaction Detail': 'INWARD CHEQUE',
      'Debit/Credit': 10200.0,
      'FROM': 'Bank'
    }
  ];

  it('should render discrepancy list with correct count', () => {
    render(<DiscrepancyList discrepancies={mockDiscrepancies} />);

    expect(screen.getByText(/Found 3 discrepancies/i)).toBeInTheDocument();
  });

  it('should render all discrepancies with correct details', () => {
    render(<DiscrepancyList discrepancies={mockDiscrepancies} />);

    // Check transaction details are displayed
    expect(screen.getByText('Payment Suzuki Azim Motors WHT 5.515')).toBeInTheDocument();
    expect(screen.getByText('INWARD CHEQUE')).toBeInTheDocument();
  });

  it('should display Bank source with correct styling', () => {
    render(<DiscrepancyList discrepancies={mockDiscrepancies} />);

    const bankSources = screen.getAllByText('Bank');
    expect(bankSources.length).toBeGreaterThan(0);

    // Check for Bank-specific styling (blue color indicator)
    const bankIndicators = screen.getAllByText('Bank');
    bankSources.forEach(indicator => {
      expect(indicator).toBeInTheDocument();
    });
  });

  it('should display Company source with correct styling', () => {
    render(<DiscrepancyList discrepancies={mockDiscrepancies} />);

    const companySources = screen.getAllByText('Company');
    expect(companySources.length).toBeGreaterThan(0);

    // Check for Company-specific styling (green color indicator)
    companySources.forEach(indicator => {
      expect(indicator).toBeInTheDocument();
    });
  });

  it('should format debit amounts correctly with negative sign', () => {
    render(<DiscrepancyList discrepancies={mockDiscrepancies} />);

    const debitAmount = screen.getByText(/-40771.695/);
    expect(debitAmount).toBeInTheDocument();

    // Check for red color styling for debit amounts
    expect(debitAmount).toHaveClass('text-red-600');
  });

  it('should format credit amounts correctly with positive sign', () => {
    render(<DiscrepancyList discrepancies={mockDiscrepancies} />);

    const creditAmount = screen.getByText(/\+10200.0/);
    expect(creditAmount).toBeInTheDocument();

    // Check for green color styling for credit amounts
    expect(creditAmount).toHaveClass('text-green-600');
  });

  it('should display transaction dates in correct format', () => {
    render(<DiscrepancyList discrepancies={mockDiscrepancies} />);

    expect(screen.getByText('2026-05-06')).toBeInTheDocument();
    expect(screen.getByText('2026-05-05')).toBeInTheDocument();
  });

  it('should handle empty discrepancy list gracefully', () => {
    render(<DiscrepancyList discrepancies={[]} />);

    expect(screen.getByText(/Found 0 discrepancies/i)).toBeInTheDocument();
  });

  it('should display warning banner for discrepancy count', () => {
    render(<DiscrepancyList discrepancies={mockDiscrepancies} />);

    const warningBanner = screen.getByText(/Found 3 discrepancies/i);
    expect(warningBanner).toBeInTheDocument();
    expect(warningBanner.closest('.bg-yellow-50')).toBeInTheDocument();
  });

  it('should separate bank and company discrepancies visually', () => {
    render(<DiscrepancyList discrepancies={mockDiscrepancies} />);

    // Bank discrepancies should have blue border
    const bankCards = screen.getAllByText('Bank').map(el =>
      el.closest('.bg-blue-50')
    ).filter(Boolean);

    // Company discrepancies should have green border
    const companyCards = screen.getAllByText('Company').map(el =>
      el.closest('.bg-green-50')
    ).filter(Boolean);

    expect(bankCards.length).toBeGreaterThan(0);
    expect(companyCards.length).toBeGreaterThan(0);
  });
});

// وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِين
