package com.neil.microservices.order.dto;

public record InventoryOrderClientRequest(String skuCode, Integer quantity) {

}
