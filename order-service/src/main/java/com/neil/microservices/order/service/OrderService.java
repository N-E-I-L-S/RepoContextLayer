package com.neil.microservices.order.service;

import com.neil.microservices.order.client.InventoryClient;
import com.neil.microservices.order.dto.InventoryOrderClientRequest;
import com.neil.microservices.order.dto.OrderRequest;
import com.neil.microservices.order.event.OrderPlacedEvent;
import com.neil.microservices.order.model.Order;
import com.neil.microservices.order.repository.OrderRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import java.util.UUID;
@Service
public class OrderService {

    private static final Logger log = LoggerFactory.getLogger(OrderService.class);
    @Autowired
    private InventoryClient inventoryClient;

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private KafkaTemplate<String, OrderPlacedEvent> kafkaTemplate;


    public void placeOrder(OrderRequest orderRequest){
       boolean productInStock = inventoryClient.isInStock(orderRequest.skuCode(), orderRequest.quantity());
       if(productInStock) {
            Order order = new Order();

            order.setOrderNumber(UUID.randomUUID().toString());
            order.setPrice(orderRequest.price());
            order.setSkuCode(orderRequest.skuCode());
            order.setQuantity(orderRequest.quantity());
            orderRepository.save(order);

            OrderPlacedEvent orderPlacedEvent = new OrderPlacedEvent(orderRequest.userDetails().email(),order.getOrderNumber());
            System.out.println(orderPlacedEvent);
            kafkaTemplate.send("order_placed", orderPlacedEvent);
            log.info("Order {} sent to kafka topic order_placed", orderPlacedEvent);

           InventoryOrderClientRequest updateQuantityRequest = new InventoryOrderClientRequest(orderRequest.skuCode(), orderRequest.quantity());
           boolean inventoryUpdated = inventoryClient.updateQuantity(updateQuantityRequest);

            if(inventoryUpdated){
                log.info("Inventory for product with skuCode {} has been updated for order placed", orderRequest.skuCode());
            }
            else{
                throw new RuntimeException("Inventory could not be updated for current order");
            }
       }
       else{
           throw  new RuntimeException("Product with skuCode "+ orderRequest.skuCode()+" is not in stock");
       }
    }
}
