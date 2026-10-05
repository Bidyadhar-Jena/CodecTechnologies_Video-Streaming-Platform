document.querySelectorAll(".thumb video").forEach(video => {
  video.addEventListener("loadedmetadata", () => {
    video.currentTime = Math.min(1, video.duration / 2);
  });
});
