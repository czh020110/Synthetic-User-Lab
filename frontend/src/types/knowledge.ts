export type RetrievalSourceType = 'product_knowledge' | 'failure_case';

export interface KnowledgeItem {
  id: string;
  source_type: RetrievalSourceType;
  title: string;
  content: string;
  keywords: string[];
  source_ref: string;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeItemCreate {
  source_type: RetrievalSourceType;
  title: string;
  content: string;
  keywords?: string[];
  source_ref?: string;
}

export interface KnowledgeItemUpdate {
  title?: string | null;
  content?: string | null;
  keywords?: string[] | null;
  source_ref?: string | null;
}
