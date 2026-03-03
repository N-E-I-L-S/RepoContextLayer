package com.neil.microservices.order.controller;

import com.neil.microservices.order.dto.OrderRequest;
import com.neil.microservices.order.service.OrderService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/order")
public class OrderController {

    @Autowired
    private OrderService orderService;

    @PostMapping
    public String placeOrder(@RequestBody OrderRequest orderRequest){
        try{
            orderService.placeOrder(orderRequest);
            return "Order Placed Successfully";
        }
        catch (Exception e){
            System.out.println("An Error Occurred");
            throw e;
        }
    }

    @GetMapping
    public String TestMapper(){
        return "Order Controller alive";
    }
}
