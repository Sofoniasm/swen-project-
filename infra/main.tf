terraform {
  required_version = ">= 1.0"
}

variable "simulate" {
  type    = bool
  default = true
  description = "If true, modules will not create real cloud resources and will use local/no-op replacements."
}

# Example: a simple local resource that simulates compute
resource "local_file" "simulate_summary" {
  content = jsonencode({
    simulate = var.simulate,
    timestamp = timestamp(),
  })
  filename = "${path.module}/simulate_summary.json"
}

output "simulate_file" {
  value = local_file.simulate_summary.filename
}
