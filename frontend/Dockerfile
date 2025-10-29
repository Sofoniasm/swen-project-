# Frontend multistage build
## Static frontend image: serve prebuilt files from `frontend/dist` using nginx
FROM nginx:stable-alpine

# Copy the built frontend (dist) into nginx content directory. The CI build
# uses the `context: ./frontend` so `dist` is available at the context root.
COPY dist/ /usr/share/nginx/html/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
