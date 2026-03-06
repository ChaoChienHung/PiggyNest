export interface User {
  id: number;
  email: string;
}

export interface PiggyBank {
  id: number;
  user_id: number;
  name: string;
}

export interface Transaction {
  id: number;
  piggy_bank_id: number;
  amount: number;
  category?: string;
  description?: string;
  date: string;
}

export interface Balance {
  balance: number;
  transaction_count: number;
}
