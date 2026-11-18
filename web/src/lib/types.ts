export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type?: string;
}

export interface Me {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
  permissions: string[];
}

export interface Attachment {
  id: string;
  kind: string;
  mime_type: string | null;
  original_name: string | null;
  size_bytes: number;
  is_quarantined: boolean;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_type: string;
  content_text: string | null;
  content_type: string;
  created_at: string;
  attachments: Attachment[];
}

export interface Conversation {
  id: string;
  branch_id: string;
  employee_id: string;
  status: string;
  ai_enabled: boolean;
  taken_over_by: string | null;
  subject: string | null;
  last_message_at: string | null;
  created_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export interface Ticket {
  id: string;
  public_code: string;
  branch_id: string;
  employee_id: string;
  conversation_id: string | null;
  category: string;
  priority: string;
  status: string;
  title: string;
  description: string | null;
  assigned_to: string | null;
  created_at: string;
}
