variable "prefix" {
    type: "string"
    description: "The prefix to use for all auditors"
    default = "audit"
}

variable "auditors" {
    type: "map"
    description: "The mapping of auditors and actions to use"
}

variable "tags" {
    type: "map"
    description: "Tags to use"
}