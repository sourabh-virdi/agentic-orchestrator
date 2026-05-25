variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "agentic-orchestrator"
}

variable "environment" {
  description = "Deployment environment (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# --- Database ---
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_storage_gb" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_password" {
  description = "Database password (use Secrets Manager in production)"
  type        = string
  sensitive   = true
}

# --- Redis ---
variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

# --- ECS ---
variable "ecr_repository_url" {
  description = "ECR repository URL for the API image"
  type        = string
}

variable "api_cpu" {
  description = "API task CPU units (256 = 0.25 vCPU)"
  type        = number
  default     = 512
}

variable "api_memory" {
  description = "API task memory in MB"
  type        = number
  default     = 1024
}

variable "api_desired_count" {
  description = "Number of API task instances"
  type        = number
  default     = 1
}
