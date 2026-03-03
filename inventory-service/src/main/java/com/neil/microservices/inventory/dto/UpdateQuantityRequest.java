package com.neil.microservices.inventory.dto;

public record UpdateQuantityRequest(String skuCode, Integer quantity) {
}
