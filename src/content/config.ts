import { defineCollection, z } from 'astro:content';

const blog = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    tags: z.array(z.string()).optional(),
    type: z.string().optional(),
    original_url: z.string().optional(),
    source: z.string().optional(),
  }),
});

export const collections = { blog };
