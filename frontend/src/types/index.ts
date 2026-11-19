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
}

export interface Balance {
  balance: number;
  transaction_count: number;
}
