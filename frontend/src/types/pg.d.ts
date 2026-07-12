declare module "pg" {
  export class Pool {
    constructor(config: { connectionString?: string; max?: number });
    connect(): Promise<any>;
    end(): Promise<void>;
    query(text: string, params?: any[]): Promise<any>;
  }
}
