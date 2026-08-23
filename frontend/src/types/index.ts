export interface User {
  id: number;
  username: string;
  email: string;
}

export interface PiggyBank {
  id: number;
  user_id: number;
  name: string;
  currency: string;
}

export interface Category {
  id: number;
  user_id: number;
  name: string;
  created_at?: string;
}

export interface Transaction {
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
