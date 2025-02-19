#!/bin/bash
set -e  # Exit on error

# Get CPU count for macOS
cpu_count=$(sysctl -n hw.ncpu)
parallel_jobs=$((cpu_count - 1))

# Function to build a single image
build_image() {
    local image_id=$1
    local image_name=$2

    # Skip if this is already an MCP image
    if [[ $image_name == *"-mcp"* ]]; then
        return 0
    fi
    
    # Create MCP tag
    local mcp_tag="${image_name/:latest/-mcp:latest}"
    
    # Run the build
    if docker build \
        --quiet \
        --build-arg BASE_IMAGE="$image_id" \
        -t "$mcp_tag" \
        -f Dockerfile.template .; then
        printf "."
        return 0
    else
        printf "❌\n"
        echo "Failed: $mcp_tag (using base image ID: $image_id)" >&2
        return 1
    fi
}
export -f build_image

# Main execution
echo "🚀 Starting parallel builds with $parallel_jobs jobs..."

# Get ONLY original images
total=$(docker images 'sweb.eval.*' --format '{{.Repository}}:{{.Tag}}' | grep -v -- '-mcp' | wc -l | tr -d ' ')
echo "📦 Found $total original SWE-bench images to process"

# Process images in parallel
echo -n "Progress: "
docker images 'sweb.eval.*' --format '{{.Repository}}:{{.Tag}}\t{{.ID}}' | \
    grep -v -- '-mcp' | \
    parallel --will-cite --keep-order \
    --colsep '\t' \
    --joblog .parallel.log \
    --jobs "$parallel_jobs" build_image {2} {1}
echo  # New line after progress dots

# Show summary
completed=$(grep "1" .parallel.log | wc -l | tr -d ' ')
echo "✨ Completed $completed/$total builds successfully!"

# Cleanup
rm -f .parallel.log