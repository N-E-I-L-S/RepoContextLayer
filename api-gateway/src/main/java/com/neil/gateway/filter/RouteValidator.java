package com.neil.gateway.filter;

import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.util.AntPathMatcher;

import java.util.List;
import java.util.function.Predicate;

@Component
public class RouteValidator {

    private static final List<String> openApiEndpoints = List.of(
            "/auth/register",
            "/auth/token",
            "/auth/validate",
            "/eureka/**"
    );

    private final AntPathMatcher pathMatcher = new AntPathMatcher();

    public Predicate<ServerHttpRequest> isSecured = request -> {
        String requestPath = request.getURI().getPath();
        return openApiEndpoints
                .stream()
                .noneMatch(publicPath -> pathMatcher.match(publicPath, requestPath));
    };
}
