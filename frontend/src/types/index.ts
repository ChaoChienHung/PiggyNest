export interface User {
  id: number;
  username: string;
  email: string;
  /** Transactions shown per page in a PiggyBank; 0 shows all. */
  transactions_per_page: number;
  /** YYYY-MM-DD, DD/MM/YYYY, or MM/DD/YYYY; the API itself always uses ISO dates. */
  date_format: string;
  display_currency: string;
  net_worth_hidden: boolean;
}

export interface PiggyBank {
  id: number;
  user_id: number;
  name: string;
  currency: string;
  is_pinned?: boolean;
}

export interface Category {
  id: number;
  user_id: number;
  name: string;
  created_at?: string;
}

export interface Transaction {
  transaction_id: string;
  id: number;
  piggy_bank_id: number;
  amount: number;
  type: string;
  category?: string;
  description?: string;
  date: string;
  recurring_rule_id?: number | null;
}

export interface PendingTransaction {
  id: number;
  piggy_bank_id: number;
  piggy_bank_name?: string | null;
  piggy_bank_currency?: string | null;
  amount: number;
  type: string;
  category?: string | null;
  description?: string | null;
  expected_date?: string | null;
  status: 'pending' | 'confirmed' | 'cancelled';
  confirmed_transaction_id?: number | null;
  created_at?: string | null;
  confirmed_at?: string | null;
}

export interface AppNotification {
  id: number;
  kind: string;
  title: string;
  body: string;
  is_read: boolean;
  event_key?: string | null;
  created_at?: string | null;
  read_at?: string | null;
}

export interface NotificationListResponse {
  items: AppNotification[];
  unread_count: number;
}

export type RecurrenceFrequency = 'daily' | 'weekly' | 'monthly' | 'yearly';
export type RecurrenceStatus = 'active' | 'paused' | 'stopped';

export interface RecurringRule {
  id: number;
  piggy_bank_id: number;
  piggy_bank_name?: string | null;
  piggy_bank_currency?: string | null;
  amount: number;
  type: string;
  category?: string | null;
  description?: string | null;
  frequency: RecurrenceFrequency;
  interval: number;
  start_date: string;
  next_run_date: string;
  end_date?: string | null;
  status: RecurrenceStatus;
  execution_count: number;
  created_at?: string | null;
}

export interface Balance {
  balance: number;
  transaction_count: number;
}
